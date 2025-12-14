# Quick Implementation Guide

This guide provides ready-to-use code for the most critical improvements.

## 1. Security Fixes

### Add Input Validation

**File:** `backend/routes/api.js`

```javascript
const express = require('express');
const router = express.Router();
const { body, param, query, validationResult } = require('express-validator');
const oddsApiService = require('../services/oddsApiService');
const promptBuilderService = require('../services/promptBuilderService');

// Validation middleware
const validate = (req, res, next) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ errors: errors.array() });
  }
  next();
};

// Get games for a sport
router.get('/games/:sportKey', [
  param('sportKey').notEmpty().isString(),
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
  body('games').isArray({ min: 1 }).withMessage('At least one game is required'),
  body('sportsbooks').isArray({ min: 1 }).withMessage('At least one sportsbook is required'),
  body('betTypes').isArray({ min: 1 }).withMessage('At least one bet type is required'),
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

// ... rest of routes

module.exports = router;
```

**Install dependency:**
```bash
npm install express-validator
```

### Configure CORS Properly

**File:** `backend/server.js`

```javascript
const express = require('express');
const cors = require('cors');
const path = require('path');
require('dotenv').config();

const apiRoutes = require('./routes/api');

const app = express();
const PORT = process.env.PORT || 3000;

// CORS configuration
const corsOptions = {
  origin: function (origin, callback) {
    const allowedOrigins = process.env.ALLOWED_ORIGINS?.split(',') || [
      'http://localhost:5173',
      'http://localhost:3000'
    ];
    
    // Allow requests with no origin (like mobile apps or curl requests)
    if (!origin) return callback(null, true);
    
    if (allowedOrigins.indexOf(origin) !== -1 || process.env.NODE_ENV === 'development') {
      callback(null, true);
    } else {
      callback(new Error('Not allowed by CORS'));
    }
  },
  credentials: true,
  optionsSuccessStatus: 200
};

// Middleware
app.use(cors(corsOptions));
app.use(express.json({ limit: '1mb' }));
app.use(express.urlencoded({ extended: true, limit: '1mb' }));

// API routes
app.use('/api', apiRoutes);

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    uptime: process.uptime()
  });
});

// Serve static files in production
if (process.env.NODE_ENV === 'production') {
  app.use(express.static(path.join(__dirname, 'public')));

  // Handle SPA routing
  app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
  });
}

// Error handler middleware
app.use((err, req, res, next) => {
  console.error('Error:', err);
  
  const status = err.status || 500;
  const message = process.env.NODE_ENV === 'production' 
    ? 'Internal server error' 
    : err.message;
  
  res.status(status).json({ 
    error: message,
    ...(process.env.NODE_ENV === 'development' && { stack: err.stack })
  });
});

const server = app.listen(PORT, () => {
  console.log(`Betting Prompt Builder API running on port ${PORT}`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM received, shutting down gracefully');
  server.close(() => {
    console.log('Server closed');
    process.exit(0);
  });
});

process.on('SIGINT', () => {
  console.log('SIGINT received, shutting down gracefully');
  server.close(() => {
    console.log('Server closed');
    process.exit(0);
  });
});
```

### Add Rate Limiting

**File:** `backend/server.js` (add after middleware setup)

```javascript
const rateLimit = require('express-rate-limit');

// General API rate limiter
const apiLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
  message: 'Too many requests from this IP, please try again later.',
  standardHeaders: true,
  legacyHeaders: false,
});

// Stricter limiter for game fetching (more expensive operation)
const gamesLimiter = rateLimit({
  windowMs: 1 * 60 * 1000, // 1 minute
  max: 20, // limit each IP to 20 requests per minute
  message: 'Too many game requests, please try again later.',
});

app.use('/api', apiLimiter);
app.use('/api/games', gamesLimiter);
```

**Install dependency:**
```bash
npm install express-rate-limit
```

## 2. Performance Improvements

### Parallelize API Calls

**File:** `frontend/src/App.vue` (replace fetchGames function)

```javascript
async function fetchGames() {
  if (!selectedSports.value.length) return

  gamesLoading.value = true
  gamesError.value = null
  games.value = []
  selectedGames.value = []

  try {
    // Fetch all sports in parallel
    const responses = await Promise.allSettled(
      selectedSports.value.map(sportKey => 
        fetch(`/api/games/${sportKey}`)
      )
    )

    const allGames = []
    const errors = []

    responses.forEach((result, index) => {
      if (result.status === 'fulfilled' && result.value.ok) {
        result.value.json().then(data => {
          const sportGames = data.games || data
          allGames.push(...sportGames)
        })
      } else {
        const sportKey = selectedSports.value[index]
        errors.push(`Failed to fetch ${sportKey}`)
      }
    })

    // Wait for all JSON parsing to complete
    await Promise.all(responses.map(r => 
      r.status === 'fulfilled' && r.value.ok 
        ? r.value.json() 
        : Promise.resolve({ games: [] })
    )).then(results => {
      games.value = results.flatMap(r => r.games || r)
    })

    if (errors.length > 0 && allGames.length === 0) {
      gamesError.value = errors.join(', ')
    } else if (errors.length > 0) {
      console.warn('Some sports failed to load:', errors)
    }
  } catch (err) {
    gamesError.value = err.message
  } finally {
    gamesLoading.value = false
  }
}
```

**Better version with proper error handling:**

```javascript
async function fetchGames() {
  if (!selectedSports.value.length) return

  gamesLoading.value = true
  gamesError.value = null
  games.value = []
  selectedGames.value = []

  try {
    // Fetch all sports in parallel
    const promises = selectedSports.value.map(async (sportKey) => {
      try {
        const response = await fetch(`/api/games/${sportKey}`)
        if (!response.ok) {
          const err = await response.json()
          throw new Error(err.error || `Failed to fetch ${sportKey}`)
        }
        const data = await response.json()
        return data.games || data
      } catch (error) {
        console.error(`Error fetching ${sportKey}:`, error)
        return [] // Return empty array on error
      }
    })

    const results = await Promise.all(promises)
    games.value = results.flat()
    
    if (games.value.length === 0) {
      gamesError.value = 'No games found for selected sports'
    }
  } catch (err) {
    gamesError.value = err.message
  } finally {
    gamesLoading.value = false
  }
}
```

## 3. State Persistence

**File:** `frontend/src/App.vue` (add to script section)

```javascript
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
// ... other imports

// ... existing code ...

// Save state to localStorage
watch(
  [selectedSports, selectedSportsbooks, selectedBetTypes, parlaySettings],
  ([sports, books, types, settings]) => {
    try {
      localStorage.setItem('betting-prompt-state', JSON.stringify({
        sports,
        books,
        types,
        settings,
        timestamp: Date.now()
      }))
    } catch (err) {
      console.warn('Failed to save state:', err)
    }
  },
  { deep: true }
)

// Load state from localStorage on mount
onMounted(() => {
  try {
    const saved = localStorage.getItem('betting-prompt-state')
    if (saved) {
      const state = JSON.parse(saved)
      // Only restore if less than 7 days old
      if (state.timestamp && Date.now() - state.timestamp < 7 * 24 * 60 * 60 * 1000) {
        if (state.sports) selectedSports.value = state.sports
        if (state.books) selectedSportsbooks.value = state.books
        if (state.types) selectedBetTypes.value = state.types
        if (state.settings) parlaySettings.value = { ...parlaySettings.value, ...state.settings }
      }
    }
  } catch (err) {
    console.warn('Failed to load saved state:', err)
  }
})
```

## 4. Configuration File

**File:** `backend/config/constants.js` (new file)

```javascript
module.exports = {
  // Cache settings
  CACHE_TTL: process.env.CACHE_TTL || 300, // 5 minutes default
  
  // API settings
  MAX_CONTENDERS: 15,
  MAX_GAMES_PER_REQUEST: 100,
  
  // Rate limiting
  RATE_LIMIT_WINDOW_MS: 15 * 60 * 1000, // 15 minutes
  RATE_LIMIT_MAX_REQUESTS: 100,
  GAMES_RATE_LIMIT_WINDOW_MS: 1 * 60 * 1000, // 1 minute
  GAMES_RATE_LIMIT_MAX_REQUESTS: 20,
  
  // Request limits
  MAX_REQUEST_SIZE: '1mb',
  
  // Sportsbooks
  DEFAULT_SPORTSBOOKS: ['draftkings', 'fanduel', 'betmgm'],
  DEFAULT_MARKETS: ['h2h', 'spreads', 'totals'],
  
  // Parlay defaults
  DEFAULT_MIN_LEGS: 2,
  DEFAULT_MAX_LEGS: 4,
  DEFAULT_MIN_ODDS: -150,
  DEFAULT_MAX_ODDS: 500
};
```

**Update:** `backend/services/oddsApiService.js`

```javascript
const NodeCache = require('node-cache');
const { CACHE_TTL } = require('../config/constants');

const BASE_URL = 'https://api.the-odds-api.com/v4';
const cache = new NodeCache({ stdTTL: CACHE_TTL }); // Use config
// ... rest of file
```

## 5. Logging

**File:** `backend/server.js` (add after middleware)

```javascript
const morgan = require('morgan');

// Logging middleware
if (process.env.NODE_ENV === 'production') {
  app.use(morgan('combined'));
} else {
  app.use(morgan('dev'));
}
```

**Install dependency:**
```bash
npm install morgan
```

## 6. .dockerignore File

**File:** `.dockerignore` (new file)

```
node_modules
npm-debug.log
.git
.gitignore
.env
.env.local
.env.*.local
*.log
.DS_Store
coverage
.nyc_output
.vscode
.idea
*.swp
*.swo
*~
README.md
REVIEW.md
IMPROVEMENTS_GUIDE.md
```

## 7. Updated package.json

**File:** `backend/package.json`

```json
{
  "name": "betting-prompt-builder-backend",
  "version": "1.0.0",
  "description": "Backend API for Betting Prompt Builder",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "node --watch server.js"
  },
  "dependencies": {
    "cors": "^2.8.5",
    "dotenv": "^16.3.1",
    "express": "^4.18.2",
    "express-rate-limit": "^7.1.5",
    "express-validator": "^7.0.1",
    "morgan": "^1.10.0",
    "node-cache": "^5.1.2"
  }
}
```

## 8. Environment Variables Template

**File:** `.env.example` (new file)

```env
# Server
PORT=3000
NODE_ENV=production

# CORS
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# API
ODDS_API_KEY=your_api_key_here

# Cache
CACHE_TTL=300

# Rate Limiting (optional overrides)
RATE_LIMIT_MAX_REQUESTS=100
GAMES_RATE_LIMIT_MAX_REQUESTS=20
```

## Implementation Order

1. **Security (Critical):**
   - Add express-validator
   - Configure CORS
   - Add rate limiting
   - Add request size limits

2. **Performance:**
   - Parallelize API calls
   - Add configuration file

3. **UX:**
   - Add state persistence
   - Add health check

4. **DevOps:**
   - Add .dockerignore
   - Add logging
   - Add graceful shutdown

## Testing the Changes

After implementing:

1. **Test rate limiting:**
   ```bash
   # Should fail after 100 requests
   for i in {1..105}; do curl http://localhost:3000/api/usage; done
   ```

2. **Test validation:**
   ```bash
   # Should return 400 error
   curl -X POST http://localhost:3000/api/generate-prompt \
     -H "Content-Type: application/json" \
     -d '{"games":[],"sportsbooks":[],"betTypes":[]}'
   ```

3. **Test health check:**
   ```bash
   curl http://localhost:3000/health
   ```

4. **Test state persistence:**
   - Select some options in the UI
   - Refresh the page
   - Options should be restored

