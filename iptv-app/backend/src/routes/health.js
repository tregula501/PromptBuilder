const express = require('express');
const { requireAuth, requireAdmin } = require('../middleware/auth');
const logger = require('../utils/logger');

const router = express.Router();

// Public health check (for Docker/monitoring)
router.get('/', (req, res) => {
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    uptime: process.uptime()
  });
});

// VPN status (requires auth)
router.get('/vpn', requireAuth, async (req, res) => {
  try {
    const vpnHealth = req.app.locals.vpnHealth;
    const status = await vpnHealth.checkVPNStatus();

    res.json(status);

  } catch (error) {
    logger.error('VPN health check error:', error);
    res.status(500).json({
      connected: false,
      error: error.message
    });
  }
});

// Playlist status (requires auth)
router.get('/playlist', requireAuth, (req, res) => {
  try {
    const playlistManager = req.app.locals.playlistManager;
    const status = playlistManager.getStatus();

    res.json(status);

  } catch (error) {
    logger.error('Playlist status error:', error);
    res.status(500).json({ error: 'Failed to get playlist status' });
  }
});

// Refresh playlist (admin only)
router.post('/playlist/refresh', requireAuth, requireAdmin, async (req, res) => {
  try {
    const playlistManager = req.app.locals.playlistManager;

    logger.info(`Manual playlist refresh triggered by ${req.user.username}`);
    const result = await playlistManager.refresh();

    res.json(result);

  } catch (error) {
    logger.error('Playlist refresh error:', error);
    res.status(500).json({ error: 'Failed to refresh playlist' });
  }
});

// Stream health report (admin only)
router.get('/streams', requireAuth, requireAdmin, (req, res) => {
  try {
    const healthChecker = req.app.locals.healthChecker;
    const report = healthChecker.getHealthReport();

    res.json(report);

  } catch (error) {
    logger.error('Stream health report error:', error);
    res.status(500).json({ error: 'Failed to get health report' });
  }
});

// Trigger manual health check (admin only)
router.post('/streams/check', requireAuth, requireAdmin, async (req, res) => {
  try {
    const healthChecker = req.app.locals.healthChecker;

    // Run in background
    healthChecker.runHealthCheck().catch(err => {
      logger.error('Manual health check failed:', err);
    });

    res.json({
      message: 'Health check started',
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    logger.error('Start health check error:', error);
    res.status(500).json({ error: 'Failed to start health check' });
  }
});

// Full system status (admin only)
router.get('/system', requireAuth, requireAdmin, async (req, res) => {
  try {
    const playlistManager = req.app.locals.playlistManager;
    const healthChecker = req.app.locals.healthChecker;
    const vpnHealth = req.app.locals.vpnHealth;

    const [vpnStatus, playlistStatus, healthReport] = await Promise.all([
      vpnHealth.checkVPNStatus(),
      Promise.resolve(playlistManager.getStatus()),
      Promise.resolve(healthChecker.getHealthReport())
    ]);

    // Add total playlist count to streams summary for accurate display
    // Combine errors with offline since errors mean the stream is unavailable
    const streamsWithTotal = {
      ...healthReport.summary,
      totalChannels: playlistStatus.channelCount,
      checked: healthReport.summary.total,
      unchecked: playlistStatus.channelCount - healthReport.summary.total,
      offline: healthReport.summary.offline + healthReport.summary.errors
    };

    res.json({
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      vpn: vpnStatus,
      playlist: playlistStatus,
      streams: streamsWithTotal,
      memory: process.memoryUsage()
    });

  } catch (error) {
    logger.error('System status error:', error);
    res.status(500).json({ error: 'Failed to get system status' });
  }
});

module.exports = router;
