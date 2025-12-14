# Betting Prompt Builder

Vue 3 + Express app that helps you select upcoming games from **The Odds API** and generate a structured “betting analysis prompt” for use with an LLM.

## Runtime model (Docker)

This project runs as **one container**:
- Builds the Vue frontend (`frontend/`) into static assets
- Copies the build output into the Express backend (`backend/public/`)
- Serves **both**:
  - **UI**: `/`
  - **API**: `/api/*`

See:
- `Dockerfile`
- `backend/server.js`
- `backend/routes/api.js`

### Local access (current setup)

`docker-compose.yml` maps container port `3000` to host port `3050`.

- Open: `http://192.168.154.158:3050`

### Reverse proxy later (SWAG)

There is a SWAG nginx config snippet in `nginx/bets.subdomain.conf`. When you’re ready to proxy:
- set `$upstream_app` to `192.168.154.158`
- set `$upstream_port` to `3050`

## Configuration (environment variables)

The backend needs:
- `ODDS_API_KEY`: The Odds API key (required for fetching games)

Optional (recommended):
- `PORT`: backend listen port inside container (default `3000`)
- `NODE_ENV`: `production` in containers (affects static serving and error verbosity)
- `ALLOWED_ORIGINS`: comma-separated list for CORS allowlist (useful when fronted by a proxy / different origin)
- `ODDS_API_CACHE_TTL_SECONDS` or `CACHE_TTL`: cache TTL for The Odds API responses (default: 300 seconds)

## API endpoints

All endpoints are served by Express in `backend/routes/api.js`.

### GET `/api/usage`

Returns The Odds API usage headers captured from the last upstream call:

```json
{ "requestsUsed": 123, "requestsRemaining": 377 }
```

### GET `/api/validate-key`

Returns whether `ODDS_API_KEY` is valid:

```json
{ "valid": true }
```

### GET `/api/games/:sportKey`

Fetches upcoming games for a given sport key.

Query params:
- `bookmakers`: comma-separated bookmaker keys (e.g. `draftkings,fanduel,betmgm`)
- `markets`: comma-separated market keys (e.g. `h2h,spreads,totals`)

Response:

```json
{ "games": [/* ... */], "usage": { "requestsUsed": 1, "requestsRemaining": 499 } }
```

Notes:
- If no bookmakers are provided, the backend will fall back to an “events only” call.
- A short in-memory cache is used to reduce upstream quota usage.

### POST `/api/generate-prompt`

Generates the final “LLM prompt” from selected games + settings.

Body shape (current UI):

```json
{
  "games": [/* game objects previously returned by /api/games */],
  "sportsbooks": ["fanduel", "draftkings"],
  "betTypes": ["h2h", "spreads", "totals"],
  "parlaySettings": {
    "betStyle": "Parlay",
    "minLegs": 2,
    "maxLegs": 4,
    "minOdds": -150,
    "maxOdds": 500,
    "excludePlayerProps": false,
    "riskLevel": "average",
    "recommendationCount": 3
  }
}
```

Response:

```json
{ "prompt": "Analyze the following matchups...\n..." }
```

### POST `/api/clear-cache`

Clears the in-memory cache used for upstream odds responses:

```json
{ "success": true }
```

## Frontend architecture (high level)

Single-page Vue app:
- `frontend/src/App.vue` orchestrates:
  - sport selection (`components/SportSelector.vue`)
  - sportsbook selection (`components/SportsbookSelector.vue`)
  - bet type selection (`components/BetTypeSelector.vue`)
  - parlay + risk settings (`components/ParlaySettings.vue`)
  - game selection (`components/GameSelector.vue`)
  - prompt output/copy (`components/PromptOutput.vue`)

Static lists (source of truth for UI options):
- `frontend/src/data/sports.js`
- `frontend/src/data/sportsbooks.js`
- `frontend/src/data/betTypes.js`

## Development notes

### Frontend dev server

Vite dev server proxies `/api` → `http://localhost:3000` (see `frontend/vite.config.js`).

### Backend dev

`backend/package.json` includes:
- `npm run dev` using `node --watch server.js`

## Docs in this repo

There are additional internal notes / prior reviews in:
- `REVIEW.md`, `REVIEW_SUMMARY.md`
- `IMPROVEMENTS_GUIDE.md`
- `PROMPT_IMPROVEMENTS.md`, `PROMPT_ENHANCEMENTS_SUMMARY.md`


