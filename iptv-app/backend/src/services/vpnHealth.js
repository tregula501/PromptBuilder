const axios = require('axios');
const { HttpProxyAgent } = require('http-proxy-agent');
const { HttpsProxyAgent } = require('https-proxy-agent');
const logger = require('../utils/logger');

class VPNHealth {
  constructor() {
    const proxyHost = process.env.VPN_PROXY_HOST || 'vpn';
    const proxyPort = process.env.VPN_PROXY_PORT || '8888';
    const proxyUrl = `http://${proxyHost}:${proxyPort}`;

    this.httpProxyAgent = new HttpProxyAgent(proxyUrl);
    this.httpsProxyAgent = new HttpsProxyAgent(proxyUrl);

    this.client = axios.create({
      httpsAgent: this.httpsProxyAgent,
      httpAgent: this.httpProxyAgent,
      timeout: 15000
    });

    // Cache VPN status for 5 minutes to avoid rate limiting
    this.cache = {
      status: null,
      timestamp: 0,
      ttl: 5 * 60 * 1000 // 5 minutes
    };
  }

  async checkVPNStatus() {
    // Return cached status if still valid
    if (this.cache.status && (Date.now() - this.cache.timestamp) < this.cache.ttl) {
      return this.cache.status;
    }

    // Try multiple IP info services in order
    const services = [
      { url: 'http://ip-api.com/json', parser: this.parseIpApi },
      { url: 'http://ipwho.is', parser: this.parseIpWhoIs },
      { url: 'http://ipinfo.io/json', parser: this.parseIpInfo }
    ];

    for (const service of services) {
      try {
        const response = await this.client.get(service.url);
        const result = service.parser.call(this, response.data);

        if (result) {
          // Cache the successful result
          this.cache.status = result;
          this.cache.timestamp = Date.now();
          return result;
        }
      } catch (error) {
        logger.warn(`VPN check via ${service.url} failed: ${error.message}`);
        continue;
      }
    }

    // All services failed - return disconnected but preserve last known status
    logger.error('All VPN health check services failed');

    if (this.cache.status) {
      // Return stale cache with warning
      return {
        ...this.cache.status,
        stale: true,
        timestamp: new Date().toISOString()
      };
    }

    return {
      connected: false,
      error: 'Could not verify VPN status',
      timestamp: new Date().toISOString()
    };
  }

  parseIpApi(data) {
    // ip-api.com format
    if (data.status === 'success') {
      const location = data.city && data.countryCode
        ? `${data.city}, ${data.countryCode}`
        : data.country || 'Unknown';

      return {
        connected: true,
        expectedRegion: data.countryCode === 'PL',
        ip: data.query,
        location,
        city: data.city,
        region: data.regionName,
        country: data.countryCode,
        provider: data.isp,
        timestamp: new Date().toISOString()
      };
    }
    return null;
  }

  parseIpWhoIs(data) {
    // ipwho.is format
    if (data.success !== false && data.ip) {
      const location = data.city && data.country_code
        ? `${data.city}, ${data.country_code}`
        : data.country || 'Unknown';

      return {
        connected: true,
        expectedRegion: data.country_code === 'PL',
        ip: data.ip,
        location,
        city: data.city,
        region: data.region,
        country: data.country_code,
        provider: data.connection?.isp || data.connection?.org,
        timestamp: new Date().toISOString()
      };
    }
    return null;
  }

  parseIpInfo(data) {
    // ipinfo.io format
    if (data.ip) {
      const location = data.city && data.country
        ? `${data.city}, ${data.country}`
        : data.country || 'Unknown';

      return {
        connected: true,
        expectedRegion: data.country === 'PL',
        ip: data.ip,
        location,
        city: data.city,
        region: data.region,
        country: data.country,
        provider: data.org,
        timestamp: new Date().toISOString()
      };
    }
    return null;
  }

  async getPublicIP() {
    try {
      const response = await this.client.get('http://ip-api.com/json');
      return response.data.query;
    } catch (error) {
      return null;
    }
  }
}

module.exports = VPNHealth;
