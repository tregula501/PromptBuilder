const axios = require('axios');
const { HttpProxyAgent } = require('http-proxy-agent');
const { HttpsProxyAgent } = require('https-proxy-agent');
const M3UParser = require('./m3uParser');
const logger = require('../utils/logger');

class PlaylistManager {
  constructor(m3uUrl) {
    this.m3uUrl = m3uUrl;
    this.parser = new M3UParser();
    this.channels = [];
    this.categories = [];
    this.channelMap = new Map();
    this.lastFetch = null;
    this.fetchError = null;

    // Create axios instance with VPN proxy (need both HTTP and HTTPS agents)
    const proxyHost = process.env.VPN_PROXY_HOST || 'vpn';
    const proxyPort = process.env.VPN_PROXY_PORT || '8888';
    const proxyUrl = `http://${proxyHost}:${proxyPort}`;

    this.httpProxyAgent = new HttpProxyAgent(proxyUrl);
    this.httpsProxyAgent = new HttpsProxyAgent(proxyUrl);
    this.client = axios.create({
      httpsAgent: this.httpsProxyAgent,
      httpAgent: this.httpProxyAgent,
      timeout: 60000,
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      }
    });

    // Non-VPN client for fallback
    this.directClient = axios.create({
      timeout: 60000,
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
      }
    });
  }

  async initialize() {
    await this.fetchPlaylist();

    // Refresh playlist every 6 hours
    setInterval(() => {
      this.fetchPlaylist();
    }, 6 * 60 * 60 * 1000);
  }

  async fetchPlaylist() {
    logger.info(`Fetching playlist from ${this.m3uUrl}`);

    try {
      // Try through VPN first
      let response;
      try {
        response = await this.client.get(this.m3uUrl);
      } catch (vpnError) {
        logger.warn('VPN fetch failed, trying direct connection:', vpnError.message);
        response = await this.directClient.get(this.m3uUrl);
      }

      const content = response.data;

      // Parse M3U content
      this.channels = this.parser.parse(content);
      this.categories = this.parser.getCategories(this.channels);

      // Build channel lookup map
      this.channelMap.clear();
      for (const channel of this.channels) {
        this.channelMap.set(channel.id, channel);
      }

      this.lastFetch = new Date();
      this.fetchError = null;

      logger.info(`Playlist loaded: ${this.channels.length} channels, ${this.categories.length} categories`);

    } catch (error) {
      this.fetchError = error.message;
      logger.error('Failed to fetch playlist:', error.message);

      // Keep existing data if available
      if (this.channels.length > 0) {
        logger.info('Using cached playlist data');
      }
    }
  }

  getChannels() {
    return this.channels;
  }

  getCategories() {
    return this.categories;
  }

  getChannel(id) {
    return this.channelMap.get(id);
  }

  searchChannels(query) {
    return this.parser.searchChannels(this.channels, query);
  }

  getChannelsByCategory(category) {
    return this.parser.filterByCategory(this.channels, category);
  }

  paginateChannels(channels, page, limit) {
    return this.parser.paginate(channels, page, limit);
  }

  getStatus() {
    return {
      channelCount: this.channels.length,
      categoryCount: this.categories.length,
      lastFetch: this.lastFetch?.toISOString() || null,
      error: this.fetchError,
      m3uUrl: this.m3uUrl,
      isRefreshing: this.isRefreshing || false
    };
  }

  async refresh() {
    if (this.isRefreshing) {
      return { success: false, message: 'Refresh already in progress' };
    }

    this.isRefreshing = true;
    try {
      await this.fetchPlaylist();
      return {
        success: true,
        message: 'Playlist refreshed successfully',
        channelCount: this.channels.length,
        categoryCount: this.categories.length
      };
    } catch (error) {
      return {
        success: false,
        message: error.message
      };
    } finally {
      this.isRefreshing = false;
    }
  }
}

module.exports = PlaylistManager;
