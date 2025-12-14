const express = require('express');
const router = express.Router();
const { body, param, query, validationResult } = require('express-validator');
const oddsApiService = require('../services/oddsApiService');
const promptBuilderService = require('../services/promptBuilderService');

function validate(req, res, next) {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ error: 'Validation failed', details: errors.array() });
  }
  return next();
}

// Get API usage stats
router.get('/usage', (req, res) => {
  const usage = oddsApiService.getApiUsage();
  res.json(usage);
});

// Validate API key
router.get('/validate-key', async (req, res) => {
  try {
    const isValid = await oddsApiService.validateApiKey();
    res.json({ valid: isValid });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get games for a sport
router.get('/games/:sportKey', [
  param('sportKey').isString().notEmpty(),
  query('bookmakers').optional().isString(),
  query('markets').optional().isString()
], validate, async (req, res) => {
  try {
    const { sportKey } = req.params;
    const { bookmakers, markets } = req.query;

    const bookmakerList = bookmakers ? bookmakers.split(',') : ['draftkings', 'fanduel', 'betmgm'];
    const marketList = markets ? markets.split(',') : ['h2h', 'spreads', 'totals'];

    const games = await oddsApiService.getUpcomingGames(sportKey, bookmakerList, marketList);
    const usage = oddsApiService.getApiUsage();

    res.json({ games, usage });
  } catch (error) {
    console.error('Error fetching games:', error);
    res.status(500).json({ error: error.message });
  }
});

// Generate prompt
router.post('/generate-prompt', [
  body('games').isArray({ min: 1 }),
  body('sportsbooks').isArray({ min: 1 }),
  body('betTypes').isArray({ min: 1 }),
  body('parlaySettings').optional().isObject()
], validate, (req, res) => {
  try {
    const {
      games,
      sportsbooks,
      betTypes,
      parlaySettings
    } = req.body;

    const prompt = promptBuilderService.generatePrompt(
      games,
      sportsbooks,
      betTypes,
      parlaySettings || { minLegs: 2, maxLegs: 4, minOdds: -150, maxOdds: 500 },
      parlaySettings?.betStyle || 'Parlay',
      parlaySettings?.excludePlayerProps || false
    );

    res.json({ prompt });
  } catch (error) {
    console.error('Error generating prompt:', error);
    res.status(500).json({ error: error.message });
  }
});

// Clear cache
router.post('/clear-cache', (req, res) => {
  try {
    oddsApiService.clearCache();
    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;
