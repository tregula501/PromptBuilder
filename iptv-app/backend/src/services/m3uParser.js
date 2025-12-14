const crypto = require('crypto');
const logger = require('../utils/logger');

class M3UParser {
  /**
   * Parse M3U playlist content into structured channel objects
   *
   * Input format:
   * #EXTM3U
   * #EXTINF:-1 tvg-id="..." tvg-name="ESPN" tvg-logo="http://..." group-title="Sports",ESPN
   * http://gohyperspeed.com/...
   *
   * Output format:
   * [{
   *   id: "hash-of-url",
   *   name: "ESPN",
   *   displayName: "ESPN",
   *   logo: "http://...",
   *   category: "Sports",
   *   url: "http://gohyperspeed.com/...",
   *   tvgId: "",
   *   tvgName: "ESPN"
   * }]
   */
  parse(content) {
    const lines = content.split('\n').map(l => l.trim());
    const channels = [];
    let currentChannel = null;

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];

      if (line.startsWith('#EXTINF:')) {
        currentChannel = this.parseExtInf(line);
      } else if ((line.startsWith('http://') || line.startsWith('https://')) && currentChannel) {
        currentChannel.url = line;
        currentChannel.id = this.generateId(currentChannel.url);
        channels.push(currentChannel);
        currentChannel = null;
      }
    }

    logger.info(`Parsed ${channels.length} channels from M3U`);
    return channels;
  }

  parseExtInf(line) {
    const tvgId = this.extractAttribute(line, 'tvg-id');
    const tvgName = this.extractAttribute(line, 'tvg-name');
    const tvgLogo = this.extractAttribute(line, 'tvg-logo');
    const groupTitle = this.extractAttribute(line, 'group-title');

    // Get display name after the last comma
    let displayName = '';
    const commaIndex = line.lastIndexOf(',');
    if (commaIndex !== -1) {
      displayName = line.substring(commaIndex + 1).trim();
    }

    return {
      name: tvgName || displayName || 'Unknown Channel',
      displayName: displayName || tvgName || 'Unknown Channel',
      logo: tvgLogo || '',
      category: groupTitle || 'Uncategorized',
      tvgId: tvgId || '',
      tvgName: tvgName || ''
    };
  }

  extractAttribute(line, attr) {
    // Match attribute="value" or attribute='value'
    const regex = new RegExp(`${attr}=["']([^"']*)["']`, 'i');
    const match = line.match(regex);
    return match ? match[1] : null;
  }

  generateId(url) {
    return crypto.createHash('md5').update(url).digest('hex').substring(0, 12);
  }

  /**
   * Get unique categories from channels
   */
  getCategories(channels) {
    const categoryMap = new Map();

    for (const channel of channels) {
      const cat = channel.category;
      if (categoryMap.has(cat)) {
        categoryMap.set(cat, categoryMap.get(cat) + 1);
      } else {
        categoryMap.set(cat, 1);
      }
    }

    return Array.from(categoryMap.entries())
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count);
  }

  /**
   * Search channels by query
   */
  searchChannels(channels, query) {
    if (!query || query.trim() === '') {
      return channels;
    }

    const lowerQuery = query.toLowerCase();
    return channels.filter(ch =>
      ch.name.toLowerCase().includes(lowerQuery) ||
      ch.displayName.toLowerCase().includes(lowerQuery) ||
      ch.category.toLowerCase().includes(lowerQuery)
    );
  }

  /**
   * Filter channels by category
   */
  filterByCategory(channels, category) {
    if (!category) return channels;
    return channels.filter(ch => ch.category === category);
  }

  /**
   * Paginate channels
   */
  paginate(channels, page = 1, limit = 50) {
    const startIndex = (page - 1) * limit;
    const endIndex = page * limit;

    return {
      data: channels.slice(startIndex, endIndex),
      pagination: {
        page,
        limit,
        total: channels.length,
        totalPages: Math.ceil(channels.length / limit),
        hasNext: endIndex < channels.length,
        hasPrev: page > 1
      }
    };
  }
}

module.exports = M3UParser;
