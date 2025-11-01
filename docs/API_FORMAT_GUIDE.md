# API Format Handling Guide

## Overview

PromptBuilder uses a **flexible adapter pattern** to handle different API response formats. This allows us to integrate multiple data sources (The Odds API, ESPN, web scraping, custom APIs) while maintaining a consistent internal data structure.

---

## Architecture

```
┌─────────────────┐
│  External APIs  │
│  (Various)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Format Adapters │  ← Normalize different formats
│  (Converts to)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Standard Models │  ← Game, OddsData, TeamStats
│   (Pydantic)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Prompt Builder  │  ← Generates AI prompts
└─────────────────┘
```

---

## How It Works

### 1. **The Odds API Format**

**Raw API Response:**
```json
{
  "id": "abc123",
  "sport_key": "americanfootball_nfl",
  "commence_time": "2025-11-01T19:00:00Z",
  "home_team": "Los Angeles Lakers",
  "away_team": "Golden State Warriors",
  "bookmakers": [
    {
      "key": "draftkings",
      "title": "DraftKings",
      "markets": [
        {
          "key": "h2h",
          "outcomes": [
            {
              "name": "Los Angeles Lakers",
              "price": 150
            },
            {
              "name": "Golden State Warriors",
              "price": -170
            }
          ]
        },
        {
          "key": "spreads",
          "outcomes": [
            {
              "name": "Los Angeles Lakers",
              "price": -110,
              "point": 3.5
            },
            {
              "name": "Golden State Warriors",
              "price": -110,
              "point": -3.5
            }
          ]
        }
      ]
    }
  ]
}
```

**After OddsAPIAdapter Processing:**
```python
Game(
    sport=SportType.NBA,
    home_team="Los Angeles Lakers",
    away_team="Golden State Warriors",
    game_time=datetime(2025, 11, 1, 19, 0),
    odds=[
        OddsData(
            sportsbook="DraftKings",
            bet_type=BetType.MONEYLINE,
            odds="+150",
            line=None
        ),
        OddsData(
            sportsbook="DraftKings",
            bet_type=BetType.SPREAD,
            odds="-110",
            line="3.5"
        ),
        # ... more odds
    ]
)
```

---

### 2. **ESPN API Format**

**Raw API Response:**
```json
{
  "events": [
    {
      "id": "401547432",
      "name": "Los Angeles Lakers at Golden State Warriors",
      "date": "2025-11-01T19:00Z",
      "competitions": [
        {
          "id": "401547432",
          "date": "2025-11-01T19:00Z",
          "competitors": [
            {
              "id": "13",
              "homeAway": "home",
              "team": {
                "id": "13",
                "displayName": "Los Angeles Lakers"
              },
              "score": "0",
              "statistics": [
                {
                  "name": "fieldGoalPct",
                  "displayValue": "45.2"
                }
              ],
              "records": [
                {
                  "summary": "42-40"
                }
              ]
            },
            {
              "id": "9",
              "homeAway": "away",
              "team": {
                "displayName": "Golden State Warriors"
              }
            }
          ],
          "venue": {
            "fullName": "Crypto.com Arena"
          }
        }
      ]
    }
  ]
}
```

**After ESPNAPIAdapter Processing:**
```python
Game(
    sport=SportType.NBA,
    home_team="Los Angeles Lakers",
    away_team="Golden State Warriors",
    game_time=datetime(2025, 11, 1, 19, 0),
    venue="Crypto.com Arena",
    home_stats=TeamStats(
        team_name="Los Angeles Lakers",
        wins=42,
        losses=40,
        additional_stats={
            "fieldGoalPct": "45.2"
        }
    ),
    away_stats=TeamStats(
        team_name="Golden State Warriors",
        wins=None,
        losses=None
    ),
    odds=[]  # ESPN doesn't provide betting odds
)
```

---

### 3. **Combining Multiple Sources**

The power of this system is that you can **merge data from multiple sources**:

```python
from app.core.data_fetcher import get_odds_api_client, get_espn_api_client
from app.core.format_adapters import AdapterFactory

# Get odds from The Odds API
odds_client = get_odds_api_client()
odds_response = odds_client.get_odds(SportType.NBA)
odds_adapter = AdapterFactory.get_adapter("odds_api")
games_with_odds = odds_adapter.adapt_to_games(odds_response.data, SportType.NBA)

# Get stats from ESPN
espn_client = get_espn_api_client()
espn_response = espn_client.get_scores(SportType.NBA)
espn_adapter = AdapterFactory.get_adapter("espn_api")
games_with_stats = espn_adapter.adapt_to_games(espn_response.data, SportType.NBA)

# Merge the data
for odds_game in games_with_odds:
    # Find matching game in ESPN data
    for stats_game in games_with_stats:
        if (odds_game.home_team == stats_game.home_team and
            odds_game.away_team == stats_game.away_team):
            # Add stats to the odds game
            odds_game.home_stats = stats_game.home_stats
            odds_game.away_stats = stats_game.away_stats
            odds_game.venue = stats_game.venue
            break

# Now games_with_odds has both odds AND stats!
```

---

## Adding Custom API Support

### Option 1: Simple Mapping (for similar JSON structures)

```python
from app.core.format_adapters import AdapterFactory

# Define field mappings
mapping = {
    "home_team": "homeTeam.name",
    "away_team": "awayTeam.name",
    "game_time": "startDateTime",
    "odds": "bettingLines"
}

# Create adapter
adapter = AdapterFactory.get_adapter("custom", mapping_config=mapping)
games = adapter.adapt_to_games(api_data, SportType.NFL)
```

### Option 2: Create Your Own Adapter (for complex formats)

```python
from app.core.format_adapters import DataAdapter, AdapterFactory
from app.core.models import Game, SportType

class MyCustomAdapter(DataAdapter):
    """Adapter for MyCustomAPI format."""

    def adapt_to_games(self, raw_data, sport: SportType):
        games = []

        for event in raw_data:
            # Your custom parsing logic here
            game = Game(
                sport=sport,
                home_team=event["home"]["fullName"],
                away_team=event["visitor"]["fullName"],
                # ... more fields
            )
            games.append(game)

        return games

# Register your adapter
AdapterFactory.register_adapter("my_api", MyCustomAdapter)

# Use it
adapter = AdapterFactory.get_adapter("my_api")
games = adapter.adapt_to_games(custom_api_data, SportType.MLB)
```

---

## Standard Data Models

All adapters convert to these **standardized Pydantic models**:

### Game
```python
class Game(BaseModel):
    sport: SportType
    league: Optional[str]
    home_team: str
    away_team: str
    game_time: Optional[datetime]
    venue: Optional[str]
    weather: Optional[str]
    home_stats: Optional[TeamStats]
    away_stats: Optional[TeamStats]
    odds: List[OddsData]
    notes: Optional[str]
```

### OddsData
```python
class OddsData(BaseModel):
    sportsbook: str
    bet_type: BetType  # MONEYLINE, SPREAD, TOTALS, etc.
    odds: str  # e.g., "+150", "-200"
    odds_format: OddsFormat  # AMERICAN, DECIMAL, FRACTIONAL
    line: Optional[str]  # For spreads/totals (e.g., "-3.5")
    timestamp: datetime
```

### TeamStats
```python
class TeamStats(BaseModel):
    team_name: str
    wins: Optional[int]
    losses: Optional[int]
    points_per_game: Optional[float]
    points_allowed_per_game: Optional[float]
    streak: Optional[str]  # "W3", "L2"
    injuries: Optional[List[str]]
    recent_form: Optional[str]
    additional_stats: Optional[Dict[str, Any]]
```

---

## Benefits of This Approach

✅ **Consistency**: All data sources produce the same internal structure
✅ **Maintainability**: Easy to add new APIs without changing core logic
✅ **Testability**: Each adapter can be tested independently
✅ **Flexibility**: Mix and match data from multiple sources
✅ **Type Safety**: Pydantic validates all data automatically
✅ **Extensibility**: Users can add custom adapters for their own sources

---

## Supported Data Sources

| Source | Adapter | Provides | Notes |
|--------|---------|----------|-------|
| The Odds API | `OddsAPIAdapter` | Betting odds, lines | Free tier: 500 req/month |
| ESPN API | `ESPNAPIAdapter` | Team stats, scores | Free, public endpoints |
| Web Scraping | `WebScrapedDataAdapter` | Custom data | Requires configuration |
| Custom API | `CustomAPIAdapter` | Varies | User-defined mapping |

---

## Example: Complete Workflow

```python
from app.core.data_fetcher import get_odds_api_client
from app.core.prompt_builder import get_prompt_builder
from app.core.models import PromptConfig, SportType, BetType, RiskLevel

# 1. Fetch data from The Odds API (automatically uses OddsAPIAdapter)
client = get_odds_api_client()
games_dict = client.get_games_with_odds([SportType.NFL, SportType.NBA])

# 2. Create prompt configuration
config = PromptConfig(
    sports=[SportType.NFL, SportType.NBA],
    max_combined_odds=400,
    bet_types=[BetType.MONEYLINE, BetType.SPREAD, BetType.TOTALS],
    risk_tolerance=RiskLevel.MEDIUM,
    include_stats=True
)

# 3. Build prompt (uses standardized Game models)
builder = get_prompt_builder()
all_games = games_dict[SportType.NFL] + games_dict[SportType.NBA]
prompt_data = builder.build_prompt(config, all_games)

# 4. Use the prompt
print(prompt_data.prompt_text)

# 5. Save to file and commit to GitHub
builder.save_prompt(prompt_data)
```

---

## Troubleshooting

### Issue: API returns unexpected format

**Solution**: Check adapter implementation or create custom adapter

```python
# Debug raw API response
import json
print(json.dumps(api_response, indent=2))

# Compare with adapter expectations
adapter = AdapterFactory.get_adapter("odds_api")
# Verify adapter can handle the format
```

### Issue: Missing data in standardized models

**Solution**: Update adapter to extract additional fields

```python
class EnhancedOddsAPIAdapter(OddsAPIAdapter):
    def _parse_event(self, event, sport):
        game = super()._parse_event(event, sport)
        # Add custom field extraction
        game.notes = event.get("custom_field", "")
        return game

AdapterFactory.register_adapter("enhanced_odds", EnhancedOddsAPIAdapter)
```

---

## Summary

The adapter pattern allows PromptBuilder to:
- Handle **any API format** by creating a simple adapter
- Maintain **one consistent data structure** internally
- **Combine data** from multiple sources seamlessly
- Stay **flexible and extensible** for future data sources

This design makes it easy to add support for new sportsbooks, stats providers, or custom data sources without touching the core prompt generation logic!
