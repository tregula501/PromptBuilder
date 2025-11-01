"""
Odds utilities for grouping, comparing, and formatting betting odds.

This module provides helper functions for working with odds data in the UI.
"""

from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import logging

from app.core.models import Game, OddsData, BetType

logger = logging.getLogger(__name__)


def group_odds_by_bet_type(game: Game) -> Dict[BetType, List[OddsData]]:
    """
    Group a game's odds by bet type.

    Args:
        game: Game object containing odds data

    Returns:
        Dictionary mapping bet types to lists of odds

    Example:
        {
            BetType.MONEYLINE: [OddsData(...), OddsData(...), ...],
            BetType.SPREAD: [OddsData(...), ...],
            BetType.TOTALS: [OddsData(...), ...]
        }
    """
    grouped = defaultdict(list)

    for odd in game.odds:
        # BetType is already a string due to use_enum_values
        grouped[odd.bet_type].append(odd)

    logger.debug(f"Grouped {len(game.odds)} odds into {len(grouped)} bet types for {game.away_team} @ {game.home_team}")
    return dict(grouped)


def compare_odds_across_sportsbooks(game: Game, bet_type: BetType) -> Dict[str, List[OddsData]]:
    """
    Organize odds by sportsbook for a specific bet type.

    Args:
        game: Game object
        bet_type: Specific bet type to compare (e.g., "moneyline")

    Returns:
        Dictionary mapping sportsbook names to their odds for this bet type

    Example:
        {
            "DraftKings": [OddsData(team="Lakers", odds="-170"), ...],
            "FanDuel": [OddsData(team="Lakers", odds="-165"), ...],
        }
    """
    by_sportsbook = defaultdict(list)

    for odd in game.odds:
        if odd.bet_type == bet_type:
            by_sportsbook[odd.sportsbook].append(odd)

    return dict(by_sportsbook)


def find_best_odds(odds_list: List[OddsData], maximize: bool = True) -> Optional[OddsData]:
    """
    Find the best odds from a list.

    Args:
        odds_list: List of OddsData objects to compare
        maximize: If True, find highest value (for positive odds).
                 If False, find least negative (for negative odds).

    Returns:
        OddsData object with best odds, or None if list is empty

    Note:
        For positive odds (+150 vs +120): +150 is better (maximize=True)
        For negative odds (-150 vs -120): -120 is better (maximize=False)
    """
    if not odds_list:
        return None

    try:
        # Convert odds to numeric values for comparison
        odds_with_values = []
        for odd in odds_list:
            value = calculate_odds_value(odd.odds)
            odds_with_values.append((value, odd))

        # Sort and return best
        if maximize:
            return max(odds_with_values, key=lambda x: x[0])[1]
        else:
            return min(odds_with_values, key=lambda x: abs(x[0]))[1]

    except Exception as e:
        logger.error(f"Error finding best odds: {e}")
        return odds_list[0] if odds_list else None


def calculate_odds_value(odds: str) -> float:
    """
    Convert American odds string to numeric value for comparison.

    Args:
        odds: American odds string (e.g., "+150", "-200")

    Returns:
        Numeric value (positive or negative float)

    Examples:
        "+150" → 150.0
        "-200" → -200.0
        "EVEN" or "+100" → 100.0
    """
    try:
        # Clean the odds string
        odds_str = odds.strip().upper()

        # Handle special cases
        if odds_str in ["EVEN", "EV"]:
            return 100.0

        # Remove '+' and convert to float
        odds_str = odds_str.replace("+", "")
        return float(odds_str)

    except (ValueError, AttributeError):
        logger.warning(f"Invalid odds format: {odds}")
        return 0.0


def format_odds_for_display(odds: OddsData) -> str:
    """
    Format odds with line for display in UI.

    Args:
        odds: OddsData object

    Returns:
        Formatted string for display

    Examples:
        Moneyline: "+150"
        Spread: "-3.5 (-110)"
        Totals: "o224.5 (-110)"
    """
    try:
        # For spreads and totals, include the line
        if odds.line:
            return f"{odds.line} ({odds.odds})"

        # For moneyline and other bets, just the odds
        return odds.odds

    except Exception as e:
        logger.error(f"Error formatting odds: {e}")
        return str(odds.odds)


def get_odds_summary(game: Game) -> Dict[str, any]:
    """
    Get a summary of available odds for a game.

    Args:
        game: Game object

    Returns:
        Dictionary with odds summary information

    Example:
        {
            "total_odds": 45,
            "sportsbooks": ["DraftKings", "FanDuel", "BetMGM"],
            "bet_types": ["moneyline", "spread", "totals"],
            "sportsbook_count": 3,
            "bet_type_count": 3
        }
    """
    sportsbooks = set()
    bet_types = set()

    for odd in game.odds:
        sportsbooks.add(odd.sportsbook)
        bet_types.add(odd.bet_type)

    return {
        "total_odds": len(game.odds),
        "sportsbooks": sorted(list(sportsbooks)),
        "bet_types": sorted(list(bet_types)),
        "sportsbook_count": len(sportsbooks),
        "bet_type_count": len(bet_types)
    }


def calculate_implied_probability(odds: str) -> Optional[float]:
    """
    Calculate implied probability from American odds.

    Args:
        odds: American odds string (e.g., "+150", "-200")

    Returns:
        Implied probability as percentage (0-100), or None if invalid

    Formula:
        Positive odds: 100 / (odds + 100)
        Negative odds: abs(odds) / (abs(odds) + 100)

    Examples:
        "+150" → 40.0% (100 / 250)
        "-200" → 66.67% (200 / 300)
    """
    try:
        odds_value = calculate_odds_value(odds)

        if odds_value >= 0:
            # Positive odds
            probability = 100 / (odds_value + 100) * 100
        else:
            # Negative odds
            probability = abs(odds_value) / (abs(odds_value) + 100) * 100

        return round(probability, 2)

    except Exception as e:
        logger.error(f"Error calculating implied probability: {e}")
        return None


def find_odds_range(odds_list: List[OddsData]) -> Tuple[Optional[OddsData], Optional[OddsData]]:
    """
    Find the range of odds (best and worst) from a list.

    Args:
        odds_list: List of OddsData objects

    Returns:
        Tuple of (best_odds, worst_odds)
    """
    if not odds_list:
        return (None, None)

    try:
        values = [(calculate_odds_value(odd.odds), odd) for odd in odds_list]

        # For positive odds, higher is better
        # For negative odds, less negative is better
        best = max(values, key=lambda x: x[0])[1]
        worst = min(values, key=lambda x: x[0])[1]

        return (best, worst)

    except Exception as e:
        logger.error(f"Error finding odds range: {e}")
        return (odds_list[0] if odds_list else None, odds_list[-1] if odds_list else None)


def get_best_odds_per_bet_type(game: Game) -> Dict[BetType, OddsData]:
    """
    Find the best available odds for each bet type in a game.

    Args:
        game: Game object

    Returns:
        Dictionary mapping bet types to their best odds

    Example:
        {
            "moneyline": OddsData(sportsbook="FanDuel", odds="+155"),
            "spread": OddsData(sportsbook="DraftKings", odds="-105"),
            "totals": OddsData(sportsbook="BetMGM", odds="-108")
        }
    """
    grouped = group_odds_by_bet_type(game)
    best_odds = {}

    for bet_type, odds_list in grouped.items():
        best = find_best_odds(odds_list, maximize=True)
        if best:
            best_odds[bet_type] = best

    return best_odds


def format_game_summary(game: Game) -> str:
    """
    Create a human-readable summary of a game.

    Args:
        game: Game object

    Returns:
        Formatted string summary

    Example:
        "Lakers vs Warriors - 7:00 PM - 45 odds from 3 books"
    """
    time_str = game.game_time.strftime("%I:%M %p") if game.game_time else "TBD"
    summary = get_odds_summary(game)

    return (f"{game.away_team} @ {game.home_team} - {time_str} - "
            f"{summary['total_odds']} odds from {summary['sportsbook_count']} books")
