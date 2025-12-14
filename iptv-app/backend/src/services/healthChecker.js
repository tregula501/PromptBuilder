const StreamProxy = require('./streamProxy');
const logger = require('../utils/logger');

class HealthChecker {
  constructor(playlistManager, db) {
    this.playlistManager = playlistManager;
    this.db = db;
    this.streamProxy = new StreamProxy();
    this.isRunning = false;

    // Configuration for rate-limit-friendly checking
    this.config = {
      channelsPerRun: 50,        // Only check 50 channels per scheduled run
      delayBetweenChecks: 3000,  // 3 seconds between individual checks
      maxAgeHours: 24,           // Re-check channels older than 24 hours
      concurrentChecks: 1        // Only 1 concurrent check to avoid rate limits
    };
  }

  /**
   * Run a rate-limit-friendly health check
   * Only checks a subset of channels that haven't been checked recently
   */
  async runHealthCheck() {
    if (this.isRunning) {
      logger.warn('Health check already in progress, skipping');
      return;
    }

    this.isRunning = true;
    logger.info('Starting rolling health check');

    const startTime = Date.now();
    const results = {
      checked: 0,
      online: 0,
      offline: 0,
      skipped: 0
    };

    try {
      const channels = this.playlistManager.getChannels();

      if (channels.length === 0) {
        logger.warn('No channels to check');
        return results;
      }

      // Get channels that need checking (not checked in last 24 hours)
      const channelsToCheck = this.getChannelsNeedingCheck(channels);

      // Only check a limited number per run
      const batch = channelsToCheck.slice(0, this.config.channelsPerRun);
      results.skipped = channels.length - batch.length;

      logger.info(`Checking ${batch.length} channels (${channelsToCheck.length} need checking, ${channels.length} total)`);

      // Check one at a time with delays to avoid rate limits
      for (let i = 0; i < batch.length; i++) {
        const channel = batch[i];

        try {
          const health = await this.streamProxy.checkStreamHealth(channel.url);

          // Store result
          this.db.prepare(`
            INSERT INTO health_checks (channel_id, status, latency_ms, error_message)
            VALUES (?, ?, ?, ?)
          `).run(
            channel.id,
            health.status,
            health.latency || null,
            health.error || null
          );

          // Update counts
          if (health.status === 'online') results.online++;
          else results.offline++;
          results.checked++;

        } catch (err) {
          results.offline++;
          results.checked++;
          logger.error(`Health check failed for ${channel.id}:`, err.message);
        }

        // Delay between checks to avoid rate limiting
        if (i < batch.length - 1) {
          await this.sleep(this.config.delayBetweenChecks);
        }

        // Log progress every 10 channels
        if ((i + 1) % 10 === 0) {
          logger.info(`Health check progress: ${i + 1}/${batch.length}`);
        }
      }

      // Cleanup old records (keep 7 days)
      await this.cleanupOldRecords();

      const duration = Math.round((Date.now() - startTime) / 1000);
      logger.info(`Health check completed in ${duration}s:`, results);

      return results;

    } catch (error) {
      logger.error('Health check failed:', error);
      throw error;
    } finally {
      this.isRunning = false;
    }
  }

  /**
   * Get channels that haven't been checked recently
   */
  getChannelsNeedingCheck(channels) {
    const maxAgeMs = this.config.maxAgeHours * 60 * 60 * 1000;
    const cutoffTime = new Date(Date.now() - maxAgeMs).toISOString();

    // Get recently checked channel IDs
    const recentlyChecked = new Set(
      this.db.prepare(`
        SELECT DISTINCT channel_id
        FROM health_checks
        WHERE checked_at > ?
      `).all(cutoffTime).map(r => r.channel_id)
    );

    // Filter to channels that need checking
    const needsCheck = channels.filter(c => !recentlyChecked.has(c.id));

    // If all channels were checked recently, return the oldest ones
    if (needsCheck.length === 0) {
      const oldestChecked = this.db.prepare(`
        SELECT channel_id, MAX(checked_at) as last_check
        FROM health_checks
        GROUP BY channel_id
        ORDER BY last_check ASC
        LIMIT ?
      `).all(this.config.channelsPerRun).map(r => r.channel_id);

      return channels.filter(c => oldestChecked.includes(c.id));
    }

    return needsCheck;
  }

  async cleanupOldRecords() {
    try {
      const result = this.db.prepare(`
        DELETE FROM health_checks
        WHERE checked_at < datetime('now', '-7 days')
      `).run();

      if (result.changes > 0) {
        logger.info(`Cleaned up ${result.changes} old health check records`);
      }
    } catch (error) {
      logger.error('Failed to cleanup old records:', error);
    }
  }

  getHealthReport() {
    try {
      // Get latest health status per channel
      const results = this.db.prepare(`
        SELECT
          channel_id,
          status,
          latency_ms,
          error_message,
          checked_at
        FROM health_checks h1
        WHERE checked_at = (
          SELECT MAX(checked_at)
          FROM health_checks h2
          WHERE h2.channel_id = h1.channel_id
        )
        ORDER BY checked_at DESC
      `).all();

      const online = results.filter(r => r.status === 'online');
      const offline = results.filter(r => r.status === 'offline');
      const errors = results.filter(r => r.status === 'error');

      const avgLatency = online.length > 0
        ? Math.round(online.reduce((sum, r) => sum + (r.latency_ms || 0), 0) / online.length)
        : 0;

      return {
        summary: {
          total: results.length,
          online: online.length,
          offline: offline.length,
          errors: errors.length,
          avgLatency,
          lastCheck: results[0]?.checked_at || null
        },
        channels: results
      };

    } catch (error) {
      logger.error('Failed to get health report:', error);
      return {
        summary: { total: 0, online: 0, offline: 0, errors: 0 },
        channels: []
      };
    }
  }

  getChannelHealth(channelId) {
    try {
      return this.db.prepare(`
        SELECT status, latency_ms, error_message, checked_at
        FROM health_checks
        WHERE channel_id = ?
        ORDER BY checked_at DESC
        LIMIT 1
      `).get(channelId);
    } catch (error) {
      return null;
    }
  }

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

module.exports = HealthChecker;
