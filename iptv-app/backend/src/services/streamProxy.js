const axios = require('axios');
const { HttpProxyAgent } = require('http-proxy-agent');
const { HttpsProxyAgent } = require('https-proxy-agent');
const logger = require('../utils/logger');

class StreamProxy {
  constructor() {
    // Create proxy agents for VPN routing (need both for HTTP and HTTPS)
    const proxyHost = process.env.VPN_PROXY_HOST || 'vpn';
    const proxyPort = process.env.VPN_PROXY_PORT || '8888';
    const proxyUrl = `http://${proxyHost}:${proxyPort}`;

    this.httpProxyAgent = new HttpProxyAgent(proxyUrl);
    this.httpsProxyAgent = new HttpsProxyAgent(proxyUrl);

    this.client = axios.create({
      httpsAgent: this.httpsProxyAgent,
      httpAgent: this.httpProxyAgent,
      timeout: 30000,
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      },
      maxRedirects: 10
    });
  }

  /**
   * Proxy a stream through VPN
   */
  async proxyStream(channelUrl, res) {
    try {
      logger.info(`Proxying stream: ${channelUrl.substring(0, 50)}...`);

      const response = await this.client.get(channelUrl, {
        responseType: 'stream',
        timeout: 60000
      });

      // Forward relevant headers
      const contentType = response.headers['content-type'] || 'application/octet-stream';
      res.set({
        'Content-Type': contentType,
        'Access-Control-Allow-Origin': '*',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
      });

      if (response.headers['content-length']) {
        res.set('Content-Length', response.headers['content-length']);
      }

      // Handle stream errors
      response.data.on('error', (err) => {
        logger.error('Stream error:', err.message);
        if (!res.headersSent) {
          res.status(500).json({ error: 'Stream error' });
        }
      });

      // Pipe stream to response
      response.data.pipe(res);

    } catch (error) {
      const statusCode = error.response?.status;
      logger.error('Stream proxy failed:', {
        message: error.message,
        code: error.code,
        response: statusCode,
        stack: error.stack?.split('\n')[0]
      });

      if (!res.headersSent) {
        // Pass through specific error codes with appropriate messages
        if (statusCode === 404) {
          res.status(404).json({
            error: 'Stream not found',
            code: 'NOT_FOUND',
            message: 'This stream is no longer available'
          });
        } else if (statusCode === 429) {
          res.status(429).json({
            error: 'Rate limited',
            code: 'RATE_LIMITED',
            message: 'Too many requests, please wait'
          });
        } else if (statusCode === 403) {
          res.status(403).json({
            error: 'Access denied',
            code: 'FORBIDDEN',
            message: 'Stream access denied'
          });
        } else {
          res.status(502).json({
            error: 'Stream unavailable',
            code: 'UNAVAILABLE',
            message: error.message || 'Unknown error'
          });
        }
      }
    }
  }

  /**
   * Get HLS playlist and rewrite URLs for proxying
   */
  async getHLSPlaylist(channelUrl, baseProxyUrl) {
    try {
      const response = await this.client.get(channelUrl, {
        responseType: 'text',
        timeout: 15000
      });

      let content = response.data;

      // If it's an HLS playlist, we might need to rewrite segment URLs
      // For now, return as-is since most IPTV services use absolute URLs
      return {
        content,
        contentType: response.headers['content-type'] || 'application/vnd.apple.mpegurl'
      };

    } catch (error) {
      logger.error('Failed to get HLS playlist:', error.message);
      throw error;
    }
  }

  /**
   * Check if a stream is healthy
   */
  async checkStreamHealth(channelUrl) {
    try {
      const start = Date.now();

      const response = await this.client.head(channelUrl, {
        timeout: 10000,
        validateStatus: (status) => status < 500
      });

      const latency = Date.now() - start;

      if (response.status >= 200 && response.status < 400) {
        return {
          status: 'online',
          latency,
          statusCode: response.status,
          contentType: response.headers['content-type']
        };
      } else {
        return {
          status: 'error',
          latency,
          statusCode: response.status,
          error: `HTTP ${response.status}`
        };
      }

    } catch (error) {
      return {
        status: 'offline',
        error: error.message,
        code: error.code
      };
    }
  }
}

module.exports = StreamProxy;
