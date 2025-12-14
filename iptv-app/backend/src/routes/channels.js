const express = require('express');
const { query, validationResult } = require('express-validator');
const { requireAuth } = require('../middleware/auth');
const logger = require('../utils/logger');

const router = express.Router();

// All routes require authentication
router.use(requireAuth);

// List all channels (paginated)
router.get('/',
  [
    query('page').optional().isInt({ min: 1 }).toInt(),
    query('limit').optional().isInt({ min: 1, max: 100 }).toInt(),
    query('category').optional().trim(),
    query('online').optional().isBoolean().toBoolean()
  ],
  (req, res) => {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
      }

      const { page = 1, limit = 50, category, online } = req.query;
      const playlistManager = req.app.locals.playlistManager;
      const healthChecker = req.app.locals.healthChecker;

      let channels = category
        ? playlistManager.getChannelsByCategory(category)
        : playlistManager.getChannels();

      // Add health status to channels
      channels = channels.map(ch => {
        const health = healthChecker.getChannelHealth(ch.id);
        return {
          ...ch,
          health: health ? {
            status: health.status,
            latency: health.latency_ms,
            lastChecked: health.checked_at
          } : null
        };
      });

      // Filter by online status if requested
      if (online === true) {
        channels = channels.filter(ch => ch.health?.status === 'online');
      }

      const result = playlistManager.paginateChannels(channels, page, limit);

      res.json(result);

    } catch (error) {
      logger.error('Get channels error:', error);
      res.status(500).json({ error: 'Failed to get channels' });
    }
  }
);

// Search channels
router.get('/search',
  [
    query('q').trim().notEmpty().withMessage('Search query is required'),
    query('page').optional().isInt({ min: 1 }).toInt(),
    query('limit').optional().isInt({ min: 1, max: 100 }).toInt()
  ],
  (req, res) => {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
      }

      const { q, page = 1, limit = 50 } = req.query;
      const playlistManager = req.app.locals.playlistManager;
      const healthChecker = req.app.locals.healthChecker;

      let channels = playlistManager.searchChannels(q);

      // Add health status
      channels = channels.map(ch => {
        const health = healthChecker.getChannelHealth(ch.id);
        return {
          ...ch,
          health: health ? {
            status: health.status,
            latency: health.latency_ms,
            lastChecked: health.checked_at
          } : null
        };
      });

      const result = playlistManager.paginateChannels(channels, page, limit);

      res.json({
        query: q,
        ...result
      });

    } catch (error) {
      logger.error('Search channels error:', error);
      res.status(500).json({ error: 'Failed to search channels' });
    }
  }
);

// Get all categories
router.get('/categories', (req, res) => {
  try {
    const playlistManager = req.app.locals.playlistManager;
    const healthChecker = req.app.locals.healthChecker;

    const categories = playlistManager.getCategories();

    // Add online count to each category
    const categoriesWithOnline = categories.map(cat => {
      const channels = playlistManager.getChannelsByCategory(cat.name);
      let onlineCount = 0;

      channels.forEach(ch => {
        const health = healthChecker.getChannelHealth(ch.id);
        if (health?.status === 'online') {
          onlineCount++;
        }
      });

      return {
        ...cat,
        onlineCount
      };
    });

    res.json({ categories: categoriesWithOnline });

  } catch (error) {
    logger.error('Get categories error:', error);
    res.status(500).json({ error: 'Failed to get categories' });
  }
});

// Get channels by category
router.get('/category/:name',
  [
    query('page').optional().isInt({ min: 1 }).toInt(),
    query('limit').optional().isInt({ min: 1, max: 100 }).toInt()
  ],
  (req, res) => {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
      }

      const { name } = req.params;
      const { page = 1, limit = 50 } = req.query;
      const playlistManager = req.app.locals.playlistManager;
      const healthChecker = req.app.locals.healthChecker;

      let channels = playlistManager.getChannelsByCategory(decodeURIComponent(name));

      // Add health status
      channels = channels.map(ch => {
        const health = healthChecker.getChannelHealth(ch.id);
        return {
          ...ch,
          health: health ? {
            status: health.status,
            latency: health.latency_ms,
            lastChecked: health.checked_at
          } : null
        };
      });

      const result = playlistManager.paginateChannels(channels, page, limit);

      res.json({
        category: name,
        ...result
      });

    } catch (error) {
      logger.error('Get category channels error:', error);
      res.status(500).json({ error: 'Failed to get category channels' });
    }
  }
);

// Get single channel
router.get('/:id', (req, res) => {
  try {
    const playlistManager = req.app.locals.playlistManager;
    const healthChecker = req.app.locals.healthChecker;

    const channel = playlistManager.getChannel(req.params.id);

    if (!channel) {
      return res.status(404).json({ error: 'Channel not found' });
    }

    const health = healthChecker.getChannelHealth(channel.id);

    res.json({
      channel: {
        ...channel,
        health: health ? {
          status: health.status,
          latency: health.latency_ms,
          lastChecked: health.checked_at
        } : null
      }
    });

  } catch (error) {
    logger.error('Get channel error:', error);
    res.status(500).json({ error: 'Failed to get channel' });
  }
});

module.exports = router;
