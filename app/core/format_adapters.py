"""
Format adapters for converting different API responses to standardized models.

This module provides a flexible adapter pattern for handling various API formats
and converting them to our standardized Pydantic models.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from app.core.models import (
    Game, OddsData, TeamStats, SportType, BetType, OddsFormat
)

logger = logging.getLogger(__name__)


class DataAdapter(ABC):
    """Base class for data format adapters."""

    @abstractmethod
    def adapt_to_games(self, raw_data: Any, sport: SportType) -> List[Game]:
        """
        Convert raw API data to list of Game objects.

        Args:
            raw_data: Raw data from API
            sport: Sport type for the data

        Returns:
            List of Game objects
        """
        pass


class OddsAPIAdapter(DataAdapter):
    """
    Adapter for The Odds API format.

    Handles conversion of The Odds API JSON responses to Game models.
    """

    # Bet market mappings (API market key → BetType enum)
    MARKET_TO_BET_TYPE = {
        # Basic markets
        "h2h": BetType.MONEYLINE,
        "spreads": BetType.SPREAD,
        "totals": BetType.TOTALS,

        # Alternate lines
        "alternate_spreads": BetType.ALTERNATE_SPREADS,
        "alternate_totals": BetType.ALTERNATE_TOTALS,
        "alternate_team_totals": BetType.ALTERNATE_TEAM_TOTALS,

        # Soccer markets
        "h2h_3_way": BetType.H2H_3_WAY,
        "btts": BetType.BTTS,
        "draw_no_bet": BetType.DRAW_NO_BET,

        # Period markets - Quarters
        "h2h_q1": BetType.H2H_Q1,
        "h2h_q2": BetType.H2H_Q2,
        "h2h_q3": BetType.H2H_Q3,
        "h2h_q4": BetType.H2H_Q4,
        "spreads_q1": BetType.SPREADS_Q1,
        "spreads_q2": BetType.SPREADS_Q2,
        "spreads_q3": BetType.SPREADS_Q3,
        "spreads_q4": BetType.SPREADS_Q4,
        "totals_q1": BetType.TOTALS_Q1,
        "totals_q2": BetType.TOTALS_Q2,
        "totals_q3": BetType.TOTALS_Q3,
        "totals_q4": BetType.TOTALS_Q4,

        # Period markets - Halves
        "h2h_h1": BetType.H2H_H1,
        "h2h_h2": BetType.H2H_H2,
        "spreads_h1": BetType.SPREADS_H1,
        "spreads_h2": BetType.SPREADS_H2,
        "totals_h1": BetType.TOTALS_H1,
        "totals_h2": BetType.TOTALS_H2,

        # Period markets - Hockey
        "h2h_p1": BetType.H2H_P1,
        "h2h_p2": BetType.H2H_P2,
        "h2h_p3": BetType.H2H_P3,

        # Period markets - Baseball
        "h2h_1st_1_innings": BetType.H2H_1ST_1_INNINGS,
        "h2h_1st_3_innings": BetType.H2H_1ST_3_INNINGS,
        "h2h_1st_5_innings": BetType.H2H_1ST_5_INNINGS,
        "h2h_1st_7_innings": BetType.H2H_1ST_7_INNINGS,

        # Player props - NFL/NCAAF
        "player_pass_yds": BetType.PLAYER_PASS_YDS,
        "player_pass_tds": BetType.PLAYER_PASS_TDS,
        "player_rush_yds": BetType.PLAYER_RUSH_YDS,
        "player_rush_tds": BetType.PLAYER_RUSH_TDS,
        "player_receptions": BetType.PLAYER_RECEPTIONS,
        "player_reception_yds": BetType.PLAYER_RECEPTION_YDS,
        "player_anytime_td": BetType.PLAYER_ANYTIME_TD,

        # Player props - NBA/WNBA/NCAAB
        "player_points": BetType.PLAYER_POINTS,
        "player_rebounds": BetType.PLAYER_REBOUNDS,
        "player_assists": BetType.PLAYER_ASSISTS,
        "player_threes": BetType.PLAYER_THREES,
        "player_blocks": BetType.PLAYER_BLOCKS,
        "player_steals": BetType.PLAYER_STEALS,
        "player_double_double": BetType.PLAYER_DOUBLE_DOUBLE,
        "player_triple_double": BetType.PLAYER_TRIPLE_DOUBLE,

        # Player props - MLB
        "batter_home_runs": BetType.BATTER_HOME_RUNS,
        "batter_hits": BetType.BATTER_HITS,
        "batter_total_bases": BetType.BATTER_TOTAL_BASES,
        "batter_rbis": BetType.BATTER_RBIS,
        "pitcher_strikeouts": BetType.PITCHER_STRIKEOUTS,
        "pitcher_hits_allowed": BetType.PITCHER_HITS_ALLOWED,
        "pitcher_earned_runs": BetType.PITCHER_EARNED_RUNS,

        # Player props - NHL
        "player_goals": BetType.PLAYER_GOALS,
        "player_anytime_goal_scorer": BetType.PLAYER_GOAL_SCORER_ANYTIME,
        "player_shots_on_goal": BetType.PLAYER_SHOTS_ON_GOAL,
    }

    def adapt_to_games(self, raw_data: Any, sport: SportType) -> List[Game]:
        """Convert The Odds API response to Game objects."""
        if not isinstance(raw_data, list):
            logger.error("Expected list for Odds API data")
            return []

        games = []
        for event_data in raw_data:
            try:
                game = self._parse_event(event_data, sport)
                if game:
                    games.append(game)
            except Exception as e:
                logger.error(f"Error parsing Odds API event: {e}")
                continue

        return games

    def _parse_event(self, event: Dict[str, Any], sport: SportType) -> Optional[Game]:
        """Parse a single event from The Odds API."""
        try:
            # Extract basic info
            home_team = event.get("home_team", "Unknown")
            away_team = event.get("away_team", "Unknown")

            # Parse game time
            game_time = None
            if event.get("commence_time"):
                game_time = datetime.fromisoformat(
                    event["commence_time"].replace("Z", "+00:00")
                )

            # Parse odds from bookmakers
            odds_list = self._parse_bookmakers(event.get("bookmakers", []))

            # Create Game object
            return Game(
                sport=sport,
                home_team=home_team,
                away_team=away_team,
                game_time=game_time,
                odds=odds_list
            )

        except Exception as e:
            logger.error(f"Error parsing Odds API event: {e}")
            return None

    def _parse_bookmakers(self, bookmakers: List[Dict]) -> List[OddsData]:
        """Parse bookmaker odds data."""
        odds_list = []

        for bookmaker in bookmakers:
            sportsbook = bookmaker.get("title", "Unknown")
            markets = bookmaker.get("markets", [])

            for market in markets:
                market_key = market.get("key")
                bet_type = self.MARKET_TO_BET_TYPE.get(market_key, BetType.MONEYLINE)
                outcomes = market.get("outcomes", [])

                for outcome in outcomes:
                    try:
                        odds_data = OddsData(
                            sportsbook=sportsbook,
                            bet_type=bet_type,
                            odds=str(outcome.get("price", "N/A")),
                            odds_format=OddsFormat.AMERICAN,
                            line=str(outcome.get("point")) if outcome.get("point") else None
                        )
                        odds_list.append(odds_data)
                    except Exception as e:
                        logger.warning(f"Error parsing odds outcome: {e}")
                        continue

        return odds_list


class ESPNAPIAdapter(DataAdapter):
    """
    Adapter for ESPN API format.

    Handles conversion of ESPN API JSON responses to Game models.
    Note: ESPN API typically doesn't include betting odds, mainly stats.
    """

    def adapt_to_games(self, raw_data: Any, sport: SportType) -> List[Game]:
        """Convert ESPN API response to Game objects."""
        if not isinstance(raw_data, dict):
            logger.error("Expected dict for ESPN API data")
            return []

        events = raw_data.get("events", [])
        games = []

        for event_data in events:
            try:
                game = self._parse_event(event_data, sport)
                if game:
                    games.append(game)
            except Exception as e:
                logger.error(f"Error parsing ESPN event: {e}")
                continue

        return games

    def _parse_event(self, event: Dict[str, Any], sport: SportType) -> Optional[Game]:
        """Parse a single event from ESPN API."""
        try:
            # Get competition data
            competitions = event.get("competitions", [])
            if not competitions:
                return None

            competition = competitions[0]
            competitors = competition.get("competitors", [])

            # Extract teams
            home_team = None
            away_team = None
            home_stats = None
            away_stats = None

            for competitor in competitors:
                team_name = competitor.get("team", {}).get("displayName", "Unknown")
                is_home = competitor.get("homeAway") == "home"

                # Build team stats
                stats = self._parse_team_stats(competitor)

                if is_home:
                    home_team = team_name
                    home_stats = stats
                else:
                    away_team = team_name
                    away_stats = stats

            if not home_team or not away_team:
                return None

            # Parse game time
            game_time = None
            if competition.get("date"):
                game_time = datetime.fromisoformat(
                    competition["date"].replace("Z", "+00:00")
                )

            # Get venue
            venue = competition.get("venue", {}).get("fullName")

            return Game(
                sport=sport,
                home_team=home_team,
                away_team=away_team,
                game_time=game_time,
                venue=venue,
                home_stats=home_stats,
                away_stats=away_stats,
                odds=[]  # ESPN doesn't provide betting odds
            )

        except Exception as e:
            logger.error(f"Error parsing ESPN event: {e}")
            return None

    def _parse_team_stats(self, competitor: Dict[str, Any]) -> TeamStats:
        """Parse team statistics from ESPN competitor data."""
        team_name = competitor.get("team", {}).get("displayName", "Unknown")
        record = competitor.get("records", [{}])[0] if competitor.get("records") else {}

        # Extract win/loss
        wins = None
        losses = None
        if record:
            summary = record.get("summary", "0-0")
            parts = summary.split("-")
            if len(parts) >= 2:
                try:
                    wins = int(parts[0])
                    losses = int(parts[1])
                except ValueError:
                    pass

        # Get score (for completed games)
        score = competitor.get("score")

        # Extract statistics
        statistics = competitor.get("statistics", [])
        stats_dict = {}
        for stat in statistics:
            name = stat.get("name")
            value = stat.get("displayValue")
            if name and value:
                stats_dict[name] = value

        return TeamStats(
            team_name=team_name,
            wins=wins,
            losses=losses,
            additional_stats=stats_dict
        )


class CustomAPIAdapter(DataAdapter):
    """
    Adapter for custom/generic API formats.

    Allows users to define their own mapping rules for custom data sources.
    """

    def __init__(self, mapping_config: Dict[str, str]):
        """
        Initialize with field mapping configuration.

        Args:
            mapping_config: Dictionary mapping our fields to API fields
                Example: {
                    "home_team": "homeTeam",
                    "away_team": "awayTeam",
                    "game_time": "startTime",
                    "odds.price": "odds.decimal"
                }
        """
        self.mapping = mapping_config

    def adapt_to_games(self, raw_data: Any, sport: SportType) -> List[Game]:
        """Convert custom API response to Game objects using mapping."""
        # This is a simplified implementation
        # In production, you'd want more sophisticated mapping logic
        logger.warning("CustomAPIAdapter requires implementation based on specific API")
        return []


class WebScrapedDataAdapter(DataAdapter):
    """
    Adapter for web-scraped data.

    Handles conversion of scraped HTML data to Game models.
    """

    def adapt_to_games(self, raw_data: Any, sport: SportType) -> List[Game]:
        """Convert scraped data to Game objects."""
        if not isinstance(raw_data, dict):
            logger.error("Expected dict for scraped data")
            return []

        # This is a placeholder - actual implementation depends on scraping structure
        logger.info("Processing scraped data")

        # Typically scraped data would be pre-processed into a similar structure
        # to one of the above APIs, then use the appropriate adapter

        return []


class AdapterFactory:
    """
    Factory for creating appropriate data adapters.

    Automatically selects the right adapter based on data source.
    """

    _adapters = {
        "odds_api": OddsAPIAdapter,
        "espn_api": ESPNAPIAdapter,
        "web_scraping": WebScrapedDataAdapter,
        "custom": CustomAPIAdapter
    }

    @classmethod
    def get_adapter(cls, source_type: str, **kwargs) -> DataAdapter:
        """
        Get the appropriate adapter for a data source.

        Args:
            source_type: Type of data source (odds_api, espn_api, etc.)
            **kwargs: Additional arguments for adapter initialization

        Returns:
            Appropriate DataAdapter instance
        """
        adapter_class = cls._adapters.get(source_type.lower())

        if not adapter_class:
            logger.warning(f"Unknown adapter type: {source_type}, using CustomAPIAdapter")
            adapter_class = CustomAPIAdapter

        return adapter_class(**kwargs) if kwargs else adapter_class()

    @classmethod
    def register_adapter(cls, name: str, adapter_class: type):
        """
        Register a new adapter type.

        Args:
            name: Name for the adapter
            adapter_class: Adapter class (must inherit from DataAdapter)
        """
        if not issubclass(adapter_class, DataAdapter):
            raise ValueError("Adapter class must inherit from DataAdapter")

        cls._adapters[name] = adapter_class
        logger.info(f"Registered new adapter: {name}")


# Example usage documentation
"""
USAGE EXAMPLES:

1. The Odds API:
    adapter = AdapterFactory.get_adapter("odds_api")
    games = adapter.adapt_to_games(api_response, SportType.NFL)

2. ESPN API:
    adapter = AdapterFactory.get_adapter("espn_api")
    games = adapter.adapt_to_games(espn_data, SportType.NBA)

3. Custom API:
    mapping = {
        "home_team": "home.name",
        "away_team": "away.name"
    }
    adapter = AdapterFactory.get_adapter("custom", mapping_config=mapping)
    games = adapter.adapt_to_games(custom_data, SportType.MLB)

4. Register new adapter:
    class MyCustomAdapter(DataAdapter):
        def adapt_to_games(self, raw_data, sport):
            # Custom implementation
            return []

    AdapterFactory.register_adapter("my_api", MyCustomAdapter)
    adapter = AdapterFactory.get_adapter("my_api")
"""
