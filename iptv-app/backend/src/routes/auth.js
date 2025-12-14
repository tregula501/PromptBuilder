const express = require('express');
const bcrypt = require('bcrypt');
const rateLimit = require('express-rate-limit');
const { body, validationResult } = require('express-validator');
const crypto = require('crypto');
const {
  generateAccessToken,
  generateRefreshToken,
  verifyToken,
  requireAuth,
  accessCookieOptions,
  refreshCookieOptions
} = require('../middleware/auth');
const logger = require('../utils/logger');

const router = express.Router();

// Strict rate limiting for login
const loginLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 5, // 5 attempts
  message: { error: 'Too many login attempts, please try again later' },
  standardHeaders: true,
  legacyHeaders: false
});

// Login
router.post('/login',
  loginLimiter,
  [
    body('username').trim().notEmpty().withMessage('Username is required'),
    body('password').notEmpty().withMessage('Password is required')
  ],
  async (req, res) => {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
      }

      const { username, password } = req.body;
      const db = req.app.locals.db;

      // Find user
      const user = db.prepare(`
        SELECT id, username, password_hash, role, is_active
        FROM users WHERE username = ?
      `).get(username);

      if (!user) {
        return res.status(401).json({ error: 'Invalid credentials' });
      }

      if (!user.is_active) {
        return res.status(401).json({ error: 'Account is disabled' });
      }

      // Verify password
      const validPassword = await bcrypt.compare(password, user.password_hash);
      if (!validPassword) {
        return res.status(401).json({ error: 'Invalid credentials' });
      }

      // Generate tokens
      const accessToken = generateAccessToken(user);
      const refreshToken = generateRefreshToken(user);

      // Store refresh token in database
      const expiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString();
      db.prepare(`
        INSERT INTO sessions (user_id, refresh_token, expires_at, ip_address, user_agent)
        VALUES (?, ?, ?, ?, ?)
      `).run(
        user.id,
        refreshToken,
        expiresAt,
        req.ip,
        req.get('user-agent')
      );

      // Update last login
      db.prepare("UPDATE users SET last_login = datetime('now') WHERE id = ?").run(user.id);

      // Set cookies
      res.cookie('accessToken', accessToken, accessCookieOptions);
      res.cookie('refreshToken', refreshToken, refreshCookieOptions);

      logger.info(`User ${username} logged in`);

      res.json({
        user: {
          id: user.id,
          username: user.username,
          role: user.role
        },
        accessToken,
        refreshToken
      });
    } catch (error) {
      logger.error('Login error:', error);
      res.status(500).json({ error: 'Login failed' });
    }
  }
);

// Logout
router.post('/logout', requireAuth, (req, res) => {
  try {
    const db = req.app.locals.db;
    const refreshToken = req.cookies.refreshToken;

    if (refreshToken) {
      db.prepare('DELETE FROM sessions WHERE refresh_token = ?').run(refreshToken);
    }

    res.clearCookie('accessToken');
    res.clearCookie('refreshToken');

    logger.info(`User ${req.user.username} logged out`);

    res.json({ message: 'Logged out successfully' });
  } catch (error) {
    logger.error('Logout error:', error);
    res.status(500).json({ error: 'Logout failed' });
  }
});

// Get current user
router.get('/me', requireAuth, (req, res) => {
  try {
    const db = req.app.locals.db;
    const user = db.prepare(`
      SELECT id, username, role, created_at, last_login
      FROM users WHERE id = ?
    `).get(req.user.userId);

    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }

    res.json({ user });
  } catch (error) {
    logger.error('Get user error:', error);
    res.status(500).json({ error: 'Failed to get user info' });
  }
});

// Update own profile
router.put('/profile',
  requireAuth,
  [
    body('username')
      .optional()
      .trim()
      .isLength({ min: 3, max: 50 })
      .withMessage('Username must be 3-50 characters')
      .matches(/^[a-zA-Z0-9_-]+$/)
      .withMessage('Username can only contain letters, numbers, underscores, and hyphens'),
    body('currentPassword')
      .optional()
      .notEmpty()
      .withMessage('Current password is required to change password'),
    body('newPassword')
      .optional()
      .isLength({ min: 8 })
      .withMessage('New password must be at least 8 characters')
  ],
  async (req, res) => {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
      }

      const { username, currentPassword, newPassword } = req.body;
      const db = req.app.locals.db;
      const userId = req.user.userId;

      // Get current user
      const user = db.prepare('SELECT id, username, password_hash FROM users WHERE id = ?').get(userId);
      if (!user) {
        return res.status(404).json({ error: 'User not found' });
      }

      const updates = [];
      const values = [];

      // Handle username change
      if (username && username !== user.username) {
        // Check if username is taken
        const existing = db.prepare('SELECT id FROM users WHERE username = ? AND id != ?').get(username, userId);
        if (existing) {
          return res.status(409).json({ error: 'Username already taken' });
        }
        updates.push('username = ?');
        values.push(username);
      }

      // Handle password change
      if (newPassword) {
        if (!currentPassword) {
          return res.status(400).json({ error: 'Current password is required to change password' });
        }

        // Verify current password
        const validPassword = await bcrypt.compare(currentPassword, user.password_hash);
        if (!validPassword) {
          return res.status(401).json({ error: 'Current password is incorrect' });
        }

        const passwordHash = await bcrypt.hash(newPassword, 12);
        updates.push('password_hash = ?');
        values.push(passwordHash);
      }

      if (updates.length === 0) {
        return res.status(400).json({ error: 'No changes to save' });
      }

      updates.push("updated_at = datetime('now')");
      values.push(userId);

      db.prepare(`UPDATE users SET ${updates.join(', ')} WHERE id = ?`).run(...values);

      // If password changed, invalidate other sessions
      if (newPassword) {
        const currentToken = req.cookies.refreshToken;
        if (currentToken) {
          db.prepare('DELETE FROM sessions WHERE user_id = ? AND refresh_token != ?').run(userId, currentToken);
        }
      }

      // Get updated user
      const updatedUser = db.prepare(`
        SELECT id, username, role, created_at, last_login
        FROM users WHERE id = ?
      `).get(userId);

      logger.info(`User ${user.username} updated their profile`);

      res.json({
        message: 'Profile updated successfully',
        user: updatedUser
      });
    } catch (error) {
      logger.error('Update profile error:', error);
      res.status(500).json({ error: 'Failed to update profile' });
    }
  }
);

// Refresh token
router.post('/refresh', async (req, res) => {
  try {
    const refreshToken = req.cookies.refreshToken || req.body.refreshToken;

    if (!refreshToken) {
      return res.status(401).json({ error: 'Refresh token required' });
    }

    const db = req.app.locals.db;

    // Verify token exists in database
    const session = db.prepare(`
      SELECT s.*, u.username, u.role, u.is_active
      FROM sessions s
      JOIN users u ON s.user_id = u.id
      WHERE s.refresh_token = ?
    `).get(refreshToken);

    if (!session) {
      return res.status(401).json({ error: 'Invalid refresh token' });
    }

    // Check if token is expired
    if (new Date(session.expires_at) < new Date()) {
      db.prepare('DELETE FROM sessions WHERE refresh_token = ?').run(refreshToken);
      return res.status(401).json({ error: 'Refresh token expired' });
    }

    // Check if user is still active
    if (!session.is_active) {
      return res.status(401).json({ error: 'Account is disabled' });
    }

    // Verify JWT
    try {
      verifyToken(refreshToken);
    } catch (err) {
      db.prepare('DELETE FROM sessions WHERE refresh_token = ?').run(refreshToken);
      return res.status(401).json({ error: 'Invalid refresh token' });
    }

    // Generate new tokens
    const user = { id: session.user_id, username: session.username, role: session.role };
    const newAccessToken = generateAccessToken(user);
    const newRefreshToken = generateRefreshToken(user);

    // Update session with new refresh token
    const newExpiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString();
    db.prepare(`
      UPDATE sessions SET refresh_token = ?, expires_at = ?
      WHERE refresh_token = ?
    `).run(newRefreshToken, newExpiresAt, refreshToken);

    // Set cookies
    res.cookie('accessToken', newAccessToken, accessCookieOptions);
    res.cookie('refreshToken', newRefreshToken, refreshCookieOptions);

    res.json({
      accessToken: newAccessToken,
      refreshToken: newRefreshToken
    });
  } catch (error) {
    logger.error('Token refresh error:', error);
    res.status(500).json({ error: 'Token refresh failed' });
  }
});

module.exports = router;
