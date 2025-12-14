const express = require('express');
const bcrypt = require('bcrypt');
const { body, validationResult } = require('express-validator');
const { requireAuth, requireAdmin } = require('../middleware/auth');
const logger = require('../utils/logger');

const router = express.Router();
const SALT_ROUNDS = 12;

// All routes require admin access
router.use(requireAuth, requireAdmin);

// List all users
router.get('/', (req, res) => {
  try {
    const db = req.app.locals.db;
    const users = db.prepare(`
      SELECT id, username, role, is_active, created_at, last_login, created_by
      FROM users
      ORDER BY created_at DESC
    `).all();

    res.json({ users });
  } catch (error) {
    logger.error('List users error:', error);
    res.status(500).json({ error: 'Failed to list users' });
  }
});

// Create new user
router.post('/',
  [
    body('username')
      .trim()
      .isLength({ min: 3, max: 50 })
      .withMessage('Username must be 3-50 characters')
      .matches(/^[a-zA-Z0-9_-]+$/)
      .withMessage('Username can only contain letters, numbers, underscores, and hyphens'),
    body('password')
      .isLength({ min: 8 })
      .withMessage('Password must be at least 8 characters'),
    body('role')
      .optional()
      .isIn(['admin', 'user'])
      .withMessage('Role must be admin or user')
  ],
  async (req, res) => {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
      }

      const { username, password, role = 'user' } = req.body;
      const db = req.app.locals.db;

      // Check if username exists
      const existing = db.prepare('SELECT id FROM users WHERE username = ?').get(username);
      if (existing) {
        return res.status(409).json({ error: 'Username already exists' });
      }

      // Hash password
      const passwordHash = await bcrypt.hash(password, SALT_ROUNDS);

      // Create user
      const result = db.prepare(`
        INSERT INTO users (username, password_hash, role, created_by)
        VALUES (?, ?, ?, ?)
      `).run(username, passwordHash, role, req.user.userId);

      logger.info(`User ${username} created by admin ${req.user.username}`);

      res.status(201).json({
        user: {
          id: result.lastInsertRowid,
          username,
          role,
          is_active: 1,
          created_at: new Date().toISOString()
        }
      });
    } catch (error) {
      logger.error('Create user error:', error);
      res.status(500).json({ error: 'Failed to create user' });
    }
  }
);

// Get single user
router.get('/:id', (req, res) => {
  try {
    const db = req.app.locals.db;
    const user = db.prepare(`
      SELECT id, username, role, is_active, created_at, last_login, created_by
      FROM users WHERE id = ?
    `).get(req.params.id);

    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }

    res.json({ user });
  } catch (error) {
    logger.error('Get user error:', error);
    res.status(500).json({ error: 'Failed to get user' });
  }
});

// Update user
router.put('/:id',
  [
    body('password')
      .optional()
      .isLength({ min: 8 })
      .withMessage('Password must be at least 8 characters'),
    body('role')
      .optional()
      .isIn(['admin', 'user'])
      .withMessage('Role must be admin or user'),
    body('is_active')
      .optional()
      .isBoolean()
      .withMessage('is_active must be a boolean')
  ],
  async (req, res) => {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
      }

      const db = req.app.locals.db;
      const userId = parseInt(req.params.id);

      // Check user exists
      const user = db.prepare('SELECT id, username FROM users WHERE id = ?').get(userId);
      if (!user) {
        return res.status(404).json({ error: 'User not found' });
      }

      // Prevent admin from disabling their own account
      if (userId === req.user.userId && req.body.is_active === false) {
        return res.status(400).json({ error: 'Cannot disable your own account' });
      }

      // Build update query
      const updates = [];
      const values = [];

      if (req.body.password) {
        const passwordHash = await bcrypt.hash(req.body.password, SALT_ROUNDS);
        updates.push('password_hash = ?');
        values.push(passwordHash);
      }

      if (req.body.role !== undefined) {
        updates.push('role = ?');
        values.push(req.body.role);
      }

      if (req.body.is_active !== undefined) {
        updates.push('is_active = ?');
        values.push(req.body.is_active ? 1 : 0);
      }

      if (updates.length === 0) {
        return res.status(400).json({ error: 'No fields to update' });
      }

      updates.push("updated_at = datetime('now')");
      values.push(userId);

      db.prepare(`UPDATE users SET ${updates.join(', ')} WHERE id = ?`).run(...values);

      // Invalidate sessions if password changed or user disabled
      if (req.body.password || req.body.is_active === false) {
        db.prepare('DELETE FROM sessions WHERE user_id = ?').run(userId);
      }

      logger.info(`User ${user.username} updated by admin ${req.user.username}`);

      // Return updated user
      const updatedUser = db.prepare(`
        SELECT id, username, role, is_active, created_at, last_login
        FROM users WHERE id = ?
      `).get(userId);

      res.json({ user: updatedUser });
    } catch (error) {
      logger.error('Update user error:', error);
      res.status(500).json({ error: 'Failed to update user' });
    }
  }
);

// Delete user
router.delete('/:id', (req, res) => {
  try {
    const db = req.app.locals.db;
    const userId = parseInt(req.params.id);

    // Prevent admin from deleting themselves
    if (userId === req.user.userId) {
      return res.status(400).json({ error: 'Cannot delete your own account' });
    }

    const user = db.prepare('SELECT username FROM users WHERE id = ?').get(userId);
    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }

    // Delete user (cascades to sessions and favorites)
    db.prepare('DELETE FROM users WHERE id = ?').run(userId);

    logger.info(`User ${user.username} deleted by admin ${req.user.username}`);

    res.json({ message: 'User deleted successfully' });
  } catch (error) {
    logger.error('Delete user error:', error);
    res.status(500).json({ error: 'Failed to delete user' });
  }
});

module.exports = router;
