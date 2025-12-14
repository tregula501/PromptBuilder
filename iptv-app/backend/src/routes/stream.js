const express = require('express');
const { requireAuth } = require('../middleware/auth');
const StreamProxy = require('../services/streamProxy');
const logger = require('../utils/logger');

const router = express.Router();
const streamProxy = new StreamProxy();

// All routes require authentication
router.use(requireAuth);

// Stream a channel (proxy through VPN)
router.get('/:channelId', async (req, res) => {
  try {
    const playlistManager = req.app.locals.playlistManager;
    const channel = playlistManager.getChannel(req.params.channelId);

    if (!channel) {
      return res.status(404).json({ error: 'Channel not found' });
    }

    logger.info(`Streaming channel: ${channel.name} (${channel.id})`);

    // Proxy the stream through VPN
    await streamProxy.proxyStream(channel.url, res);

  } catch (error) {
    logger.error('Stream error:', error);
    if (!res.headersSent) {
      res.status(500).json({ error: 'Stream failed' });
    }
  }
});

// Get HLS playlist for a channel
router.get('/:channelId/m3u8', async (req, res) => {
  try {
    const playlistManager = req.app.locals.playlistManager;
    const channel = playlistManager.getChannel(req.params.channelId);

    if (!channel) {
      return res.status(404).json({ error: 'Channel not found' });
    }

    // For most IPTV services, the URL itself serves the stream
    // We'll redirect to our proxy endpoint
    const proxyUrl = `/api/stream/${channel.id}`;

    // Return a simple M3U8 playlist pointing to our proxy
    const playlist = `#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:BANDWIDTH=2000000
${proxyUrl}`;

    res.set({
      'Content-Type': 'application/vnd.apple.mpegurl',
      'Access-Control-Allow-Origin': '*',
      'Cache-Control': 'no-cache'
    });

    res.send(playlist);

  } catch (error) {
    logger.error('Get playlist error:', error);
    res.status(500).json({ error: 'Failed to get playlist' });
  }
});

// Get channel info for player
router.get('/:channelId/info', (req, res) => {
  try {
    const playlistManager = req.app.locals.playlistManager;
    const healthChecker = req.app.locals.healthChecker;
    const channel = playlistManager.getChannel(req.params.channelId);

    if (!channel) {
      return res.status(404).json({ error: 'Channel not found' });
    }

    const health = healthChecker.getChannelHealth(channel.id);

    res.json({
      id: channel.id,
      name: channel.name,
      logo: channel.logo,
      category: channel.category,
      streamUrl: `/api/stream/${channel.id}`,
      health: health ? {
        status: health.status,
        latency: health.latency_ms,
        lastChecked: health.checked_at
      } : null
    });

  } catch (error) {
    logger.error('Get channel info error:', error);
    res.status(500).json({ error: 'Failed to get channel info' });
  }
});

module.exports = router;
