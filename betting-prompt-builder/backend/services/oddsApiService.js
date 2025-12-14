const NodeCache = require('node-cache');

const BASE_URL = 'https://api.the-odds-api.com/v4';
const cacheTtlSeconds = parseInt(process.env.ODDS_API_CACHE_TTL_SECONDS || process.env.CACHE_TTL || '300', 10);
const cache = new NodeCache({ stdTTL: Number.isFinite(cacheTtlSeconds) ? cacheTtlSeconds : 300 });

let requestsUsed = null;
let requestsRemaining = null;

function updateApiUsage(headers) {
  const used = headers.get('x-requests-used');
  const remaining = headers.get('x-requests-remaining');

  if (used) requestsUsed = parseInt(used);
  if (remaining) requestsRemaining = parseInt(remaining);
}

function getApiUsage() {
  return { requestsUsed, requestsRemaining };
}

async function getUpcomingGames(sportKey, bookmakers, markets) {
  const apiKey = process.env.ODDS_API_KEY;
  if (!apiKey) {
    throw new Error('ODDS_API_KEY is not set');
  }

  const bookmakerList = bookmakers.filter(b => b).join(',');
  let marketList = markets.filter(m => m).join(',');

  // For golf (outrights), don't specify markets
  if (sportKey.startsWith('golf_')) {
    marketList = '';
  }

  // Check cache after normalization (important for golf where markets are forced to empty)
  const cacheKey = `games_${sportKey}_${bookmakerList}_${marketList}`;
  const cachedGames = cache.get(cacheKey);
  if (cachedGames) {
    console.log(`Returning cached games for sport: ${sportKey}`);
    return cachedGames;
  }

  // If no bookmakers available in API, just get events
  if (!bookmakerList) {
    return await getEventsOnly(sportKey);
  }

  // Build URL
  let url = `${BASE_URL}/sports/${sportKey}/odds?apiKey=${apiKey}&regions=us&oddsFormat=american&dateFormat=iso`;

  if (bookmakerList) {
    url += `&bookmakers=${bookmakerList}`;
  }

  if (marketList) {
    url += `&markets=${marketList}`;
  }

  try {
    console.log(`Fetching games for sport: ${sportKey}`);
    const response = await fetch(url);

    // Update API usage from headers
    updateApiUsage(response.headers);

    // Handle rate limiting
    if (response.status === 429) {
      const retryAfter = response.headers.get('retry-after') || 60;
      throw new Error(`API rate limit exceeded. Please wait ${retryAfter} seconds before trying again.`);
    }

    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }

    const apiGames = await response.json();
    if (!apiGames || !Array.isArray(apiGames)) {
      console.log(`No games returned from API for ${sportKey}`);
      return [];
    }

    // Filter to future games only
    const now = new Date();
    const games = apiGames
      .filter(g => new Date(g.commence_time) > now)
      .map(mapApiGameToGame);

    // Cache the results
    cache.set(cacheKey, games);

    console.log(`Successfully fetched ${games.length} games for ${sportKey}`);
    return games;
  } catch (error) {
    console.error(`Error fetching games for ${sportKey}:`, error);
    throw new Error(`Error fetching games for ${sportKey}: ${error.message}`);
  }
}

async function getEventsOnly(sportKey) {
  const apiKey = process.env.ODDS_API_KEY;
  if (!apiKey) {
    throw new Error('ODDS_API_KEY is not set');
  }

  const cacheKey = `events_${sportKey}`;
  const cached = cache.get(cacheKey);
  if (cached) {
    console.log(`Returning cached events for sport: ${sportKey}`);
    return cached;
  }

  const url = `${BASE_URL}/sports/${sportKey}/events?apiKey=${apiKey}&dateFormat=iso`;

  try {
    const response = await fetch(url);
    updateApiUsage(response.headers);

    if (response.status === 429) {
      const retryAfter = response.headers.get('retry-after') || 60;
      throw new Error(`API rate limit exceeded. Please wait ${retryAfter} seconds before trying again.`);
    }

    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }

    const apiGames = await response.json();
    if (!apiGames || !Array.isArray(apiGames)) {
      return [];
    }

    const now = new Date();
    const games = apiGames
      .filter(g => new Date(g.commence_time) > now)
      .map(mapApiGameToGame);

    cache.set(cacheKey, games);
    return games;
  } catch (error) {
    throw new Error(`Error fetching events for ${sportKey}: ${error.message}`);
  }
}

async function validateApiKey() {
  const apiKey = process.env.ODDS_API_KEY;
  if (!apiKey) {
    return false;
  }

  try {
    const url = `${BASE_URL}/sports?apiKey=${apiKey}`;
    const response = await fetch(url);
    updateApiUsage(response.headers);
    return response.ok;
  } catch {
    return false;
  }
}

function mapApiGameToGame(apiGame) {
  return {
    id: apiGame.id,
    sportKey: apiGame.sport_key,
    sportTitle: apiGame.sport_title,
    commenceTime: apiGame.commence_time,
    homeTeam: apiGame.home_team,
    awayTeam: apiGame.away_team,
    bookmakers: (apiGame.bookmakers || []).map(b => ({
      key: b.key,
      title: b.title,
      lastUpdate: b.last_update,
      markets: (b.markets || []).map(m => ({
        key: m.key,
        lastUpdate: m.last_update,
        outcomes: (m.outcomes || []).map(o => ({
          name: o.name,
          description: o.description,
          price: o.price,
          point: o.point
        }))
      }))
    }))
  };
}

function clearCache() {
  cache.flushAll();
}

module.exports = {
  getUpcomingGames,
  getEventsOnly,
  validateApiKey,
  getApiUsage,
  clearCache
};
