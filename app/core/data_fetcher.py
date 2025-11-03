"""
Data fetching module for sports and betting data from various APIs.
"""

import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from functools import lru_cache
import time

from app.core.config import get_config
from app.core.models import (
    Game, OddsData, TeamStats, SportType, BetType,
    OddsFormat, APIResponse, DataSource
)
from app.core.format_adapters import AdapterFactory

logger = logging.getLogger(__name__)


class OddsAPIClient:
    """Client for The Odds API."""

    BASE_URL = "https://api.the-odds-api.com/v4"

    # Rate limiting and caching constants
    RATE_LIMIT_SECONDS = 1.0  # Minimum seconds between API requests
    CACHE_DURATION_MINUTES = 15  # How long to cache API responses

    # Sport mappings for The Odds API
    SPORT_KEYS = {
        SportType.NFL: "americanfootball_nfl",
        SportType.NBA: "basketball_nba",
        SportType.WNBA: "basketball_wnba",
        SportType.MLB: "baseball_mlb",
        SportType.NHL: "icehockey_nhl",
        SportType.NCAAF: "americanfootball_ncaaf",
        SportType.NCAAB: "basketball_ncaab",
        SportType.SOCCER: "soccer_epl",  # Default to Premier League
        SportType.PREMIER_LEAGUE: "soccer_epl",
        SportType.LA_LIGA: "soccer_spain_la_liga",
        SportType.CHAMPIONS_LEAGUE: "soccer_uefa_champs_league",
        SportType.MLS: "soccer_usa_mls",
        SportType.MMA: "mma_mixed_martial_arts",
        SportType.UFC: "mma_mixed_martial_arts",
    }

    def __init__(self):
        self.config = get_config()
        self.api_key = self.config.odds_api_key
        self.timeout = self.config.request_timeout
        self.max_retries = self.config.max_retries
        self._request_count = 0
        self._last_request_time = None

        # Response cache: {cache_key: (response, timestamp)}
        self._cache: Dict[str, tuple[APIResponse, datetime]] = {}
        self._cache_duration = timedelta(minutes=self.CACHE_DURATION_MINUTES)

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> APIResponse:
        """Make an API request with retry logic and rate limiting."""
        if not self.api_key:
            logger.error("Odds API key not configured")
            return APIResponse(
                success=False,
                error="API key not configured. Please add ODDS_API_KEY to .env file",
                source=DataSource.ODDS_API
            )

        # Rate limiting: Wait at least RATE_LIMIT_SECONDS between requests
        if self._last_request_time:
            elapsed = time.time() - self._last_request_time
            if elapsed < self.RATE_LIMIT_SECONDS:
                time.sleep(self.RATE_LIMIT_SECONDS - elapsed)

        url = f"{self.BASE_URL}/{endpoint}"
        params = params or {}
        params["apiKey"] = self.api_key

        for attempt in range(self.max_retries):
            try:
                self._last_request_time = time.time()
                self._request_count += 1

                logger.info(f"API Request #{self._request_count}: {endpoint}")
                response = requests.get(url, params=params, timeout=self.timeout)

                # Check remaining requests
                remaining = response.headers.get("x-requests-remaining")
                if remaining:
                    logger.info(f"Requests remaining: {remaining}")

                response.raise_for_status()

                return APIResponse(
                    success=True,
                    data=response.json(),
                    source=DataSource.ODDS_API
                )

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:  # Rate limit
                    logger.warning(f"Rate limit reached, attempt {attempt + 1}/{self.max_retries}")
                    time.sleep(2 ** attempt)  # Exponential backoff
                elif e.response.status_code == 401:
                    return APIResponse(
                        success=False,
                        error="Invalid API key",
                        source=DataSource.ODDS_API
                    )
                else:
                    logger.error(f"HTTP error: {e}")
            except requests.exceptions.Timeout:
                logger.warning(f"Request timeout, attempt {attempt + 1}/{self.max_retries}")
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                break

        return APIResponse(
            success=False,
            error=f"Failed after {self.max_retries} attempts",
            source=DataSource.ODDS_API
        )

    def get_available_sports(self) -> APIResponse:
        """Get list of available sports."""
        return self._make_request("sports")

    @staticmethod
    def bet_types_to_markets(bet_types: List['BetType']) -> str:
        """
        Convert a list of BetType enums to API market parameter string.

        Args:
            bet_types: List of BetType enums

        Returns:
            Comma-separated string of API market names
        """
        from app.core.models import BET_TYPE_TO_API_MARKET, BetType

        # Filter out client-side only bet types (parlay, teaser, live)
        client_side_types = {BetType.PARLAY, BetType.TEASER, BetType.LIVE, BetType.OVER_UNDER}

        markets = []
        for bet_type in bet_types:
            if bet_type in client_side_types:
                continue  # Skip client-side only types

            api_market = BET_TYPE_TO_API_MARKET.get(bet_type)
            if api_market and api_market not in markets:
                markets.append(api_market)

        return ",".join(markets) if markets else "h2h,spreads,totals"  # Default fallback

    def get_odds(
        self,
        sport: SportType,
        regions: str = "us",
        markets: str = "h2h,spreads,totals",
        odds_format: str = "american"
    ) -> APIResponse:
        """
        Get odds for a specific sport with automatic caching.

        Responses are cached for 15 minutes to reduce API calls and improve performance.

        Args:
            sport: Sport type to get odds for
            regions: Betting regions (us, uk, eu, au)
            markets: Bet markets (h2h=moneyline, spreads, totals)
            odds_format: Odds format (american, decimal, fractional)
        """
        sport_key = self.SPORT_KEYS.get(sport)
        if not sport_key:
            return APIResponse(
                success=False,
                error=f"Sport {sport} not supported",
                source=DataSource.ODDS_API
            )

        # Create cache key from request parameters
        cache_key = f"{sport_key}:{regions}:{markets}:{odds_format}"

        # Check cache first
        if cache_key in self._cache:
            cached_response, cached_time = self._cache[cache_key]
            age = datetime.now() - cached_time

            if age < self._cache_duration:
                logger.info(f"Using cached data for {sport_key} (age: {age.seconds}s)")
                return cached_response
            else:
                # Cache expired, remove it
                del self._cache[cache_key]
                logger.debug(f"Cache expired for {sport_key}, fetching fresh data")

        # Fetch fresh data
        params = {
            "regions": regions,
            "markets": markets,
            "oddsFormat": odds_format
        }

        response = self._make_request(f"sports/{sport_key}/odds", params)

        # Cache successful responses only
        if response.success:
            self._cache[cache_key] = (response, datetime.now())
            logger.debug(f"Cached response for {sport_key}")

        return response

    def parse_odds_to_games(self, odds_response: APIResponse, sport: SportType) -> List[Game]:
        """
        Parse API response into Game objects using the OddsAPIAdapter.

        This method now uses the adapter pattern for better maintainability
        and consistency across different data sources.
        """
        if not odds_response.success or not odds_response.data:
            return []

        # Use the OddsAPIAdapter to convert raw data to Game objects
        adapter = AdapterFactory.get_adapter("odds_api")
        games = adapter.adapt_to_games(odds_response.data, sport)

        logger.info(f"Parsed {len(games)} games for {sport}")
        return games

    def get_games_with_odds(self, sports: List[SportType]) -> Dict[SportType, List[Game]]:
        """Get games with odds for multiple sports."""
        results = {}

        for sport in sports:
            logger.info(f"Fetching odds for {sport}")
            odds_response = self.get_odds(sport)

            if odds_response.success:
                games = self.parse_odds_to_games(odds_response, sport)
                results[sport] = games
                logger.info(f"Retrieved {len(games)} games for {sport}")
            else:
                logger.error(f"Failed to get odds for {sport}: {odds_response.error}")
                results[sport] = []

        return results

    def get_request_count(self) -> int:
        """Get the number of API requests made this session."""
        return self._request_count


class ESPNAPIClient:
    """Client for ESPN API (unofficial/public endpoints)."""

    BASE_URL = "https://site.api.espn.com/apis/site/v2/sports"

    # Sport mappings for ESPN
    SPORT_PATHS = {
        SportType.NFL: "football/nfl",
        SportType.NBA: "basketball/nba",
        SportType.MLB: "baseball/mlb",
        SportType.NHL: "hockey/nhl",
        SportType.NCAAF: "football/college-football",
        SportType.NCAAB: "basketball/mens-college-basketball",
    }

    def __init__(self):
        self.config = get_config()
        self.timeout = self.config.request_timeout

    def get_scores(self, sport: SportType) -> APIResponse:
        """Get scores and basic game info from ESPN."""
        sport_path = self.SPORT_PATHS.get(sport)
        if not sport_path:
            return APIResponse(
                success=False,
                error=f"Sport {sport} not supported by ESPN client",
                source=DataSource.ESPN_API
            )

        url = f"{self.BASE_URL}/{sport_path}/scoreboard"

        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()

            return APIResponse(
                success=True,
                data=response.json(),
                source=DataSource.ESPN_API
            )
        except Exception as e:
            logger.error(f"ESPN API error: {e}")
            return APIResponse(
                success=False,
                error=str(e),
                source=DataSource.ESPN_API
            )


# Singleton instances
_odds_api_client: Optional[OddsAPIClient] = None
_espn_api_client: Optional[ESPNAPIClient] = None


def get_odds_api_client() -> OddsAPIClient:
    """Get the Odds API client singleton."""
    global _odds_api_client
    if _odds_api_client is None:
        _odds_api_client = OddsAPIClient()
    return _odds_api_client


def get_espn_api_client() -> ESPNAPIClient:
    """Get the ESPN API client singleton."""
    global _espn_api_client
    if _espn_api_client is None:
        _espn_api_client = ESPNAPIClient()
    return _espn_api_client
