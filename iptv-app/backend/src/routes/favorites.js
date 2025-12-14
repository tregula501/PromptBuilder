const express = require('express');
const { requireAuth } = require('../middleware/auth');
const logger = require('../utils/logger');

const router = express.Router();

// All routes require authentication
router.use(requireAuth);

// Get user's favorites
router.get('/', (req, res) => {
  try {
    const db = req.app.locals.db;
    const playlistManager = req.app.locals.playlistManager;
    const healthChecker = req.app.locals.healthChecker;

    // Get favorite channel IDs
    const favorites = db.prepare(`
      SELECT channel_id, created_at
      FROM favorites
      WHERE user_id = ?
      ORDER BY created_at DESC
    `).all(req.user.userId);

    // Get full channel details
    const channels = favorites.map(fav => {
      const channel = playlistManager.getChannel(fav.channel_id);
      if (!channel) return null;

      const health = healthChecker.getChannelHealth(channel.id);
      return {
        ...channel,
        favoritedAt: fav.created_at,
        health: health ? {
          status: health.status,
          latency: health.latency_ms,
          lastChecked: health.checked_at
        } : null
      };
    }).filter(Boolean);

    res.json({
      favorites: channels,
      count: channels.length
    });

  } catch (error) {
    logger.error('Get favorites error:', error);
    res.status(500).json({ error: 'Failed to get favorites' });
  }
});

// Add to favorites
router.post('/:channelId', (req, res) => {
  try {
    const db = req.app.locals.db;
    const playlistManager = req.app.locals.playlistManager;
    const channelId = req.params.channelId;

    // Verify channel exists
    const channel = playlistManager.getChannel(channelId);
    if (!channel) {
      return res.status(404).json({ error: 'Channel not found' });
    }

    // Check if already favorited
    const existing = db.prepare(`
      SELECT id FROM favorites
      WHERE user_id = ? AND channel_id = ?
    `).get(req.user.userId, channelId);

    if (existing) {
      return res.status(409).json({ error: 'Channel already in favorites' });
    }

    // Add to favorites
    db.prepare(`
      INSERT INTO favorites (user_id, channel_id)
      VALUES (?, ?)
    `).run(req.user.userId, channelId);

    logger.info(`User ${req.user.username} added ${channel.name} to favorites`);

    res.status(201).json({
      message: 'Added to favorites',
      channel: {
        id: channel.id,
        name: channel.name
      }
    });

  } catch (error) {
    logger.error('Add favorite error:', error);
    res.status(500).json({ error: 'Failed to add favorite' });
  }
});

// Remove from favorites
router.delete('/:channelId', (req, res) => {
  try {
    const db = req.app.locals.db;
    const channelId = req.params.channelId;

    const result = db.prepare(`
      DELETE FROM favorites
      WHERE user_id = ? AND channel_id = ?
    `).run(req.user.userId, channelId);

    if (result.changes === 0) {
      return res.status(404).json({ error: 'Favorite not found' });
    }

    logger.info(`User ${req.user.username} removed channel ${channelId} from favorites`);

    res.json({ message: 'Removed from favorites' });

  } catch (error) {
    logger.error('Remove favorite error:', error);
    res.status(500).json({ error: 'Failed to remove favorite' });
  }
});

// Check if channel is favorited
router.get('/:channelId/check', (req, res) => {
  try {
    const db = req.app.locals.db;
    const channelId = req.params.channelId;

    const favorite = db.prepare(`
      SELECT id FROM favorites
      WHERE user_id = ? AND channel_id = ?
    `).get(req.user.userId, channelId);

    res.json({ isFavorite: !!favorite });

  } catch (error) {
    logger.error('Check favorite error:', error);
    res.status(500).json({ error: 'Failed to check favorite' });
  }
});

module.exports = router;
