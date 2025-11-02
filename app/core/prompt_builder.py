"""
Core prompt building logic for generating AI-ready betting analysis prompts.
"""

from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from app.core.config import get_config
from app.core.models import (
    Game, PromptConfig, PromptData, BetType,
    Parlay, SportType, RiskLevel, AnalysisType
)
from app.core.odds_utils import calculate_implied_probability
from app.core.timezone_utils import format_game_time

logger = logging.getLogger(__name__)


class PromptBuilder:
    """Builds AI prompts for sports betting analysis."""

    def __init__(self):
        self.config = get_config()
        self.templates_dir = self.config.TEMPLATES_DIR
        self.default_template = self._load_template("default_template.txt")

    def _load_template(self, template_name: str) -> str:
        """Load a prompt template from file."""
        template_path = self.templates_dir / template_name

        if not template_path.exists():
            logger.warning(f"Template not found: {template_name}, using fallback")
            return self._get_fallback_template()

        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error loading template: {e}")
            return self._get_fallback_template()

    def _get_fallback_template(self) -> str:
        """Get a basic fallback template."""
        return """=== AI SPORTS BETTING ANALYSIS PROMPT ===

GAME DATA:
{game_data}

ODDS DATA:
{odds_data}

Please analyze these betting opportunities considering value, risk, and statistics.
"""

    def build_prompt(self, prompt_config: PromptConfig, games: List[Game]) -> PromptData:
        """Build a complete prompt from configuration and game data."""
        logger.info(f"Building prompt for {len(games)} games")

        # Format game data
        game_data_str = self._format_game_data(games, prompt_config)

        # Format odds data with sportsbook filtering
        selected_books = prompt_config.selected_sportsbooks if prompt_config.selected_sportsbooks else None
        odds_data_str = self._format_odds_data(games, selected_books)

        # Build additional constraints
        constraints = self._build_constraints(prompt_config)

        # Build contextual factors list
        contextual_factors = self._build_contextual_factors(prompt_config)

        # Build dynamic analysis sections
        analysis_sections = self._build_analysis_sections(prompt_config)

        # Format template
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        prompt_text = self.default_template.format(
            timestamp=timestamp,
            sports=", ".join(prompt_config.sports),  # Already strings due to use_enum_values
            max_odds=f"+{prompt_config.max_combined_odds}",
            bet_types=", ".join(prompt_config.bet_types),  # Already strings
            risk_level=prompt_config.risk_tolerance,  # Already string
            game_data=game_data_str,
            odds_data=odds_data_str,
            additional_constraints=constraints,
            contextual_factors=contextual_factors,
            analysis_sections=analysis_sections,
            custom_context=prompt_config.custom_context or "None provided"
        )

        # Create PromptData object
        prompt_data = PromptData(
            config=prompt_config,
            games=games,
            prompt_text=prompt_text,
            metadata={
                "num_games": len(games),
                "timestamp": timestamp,
                "template": "default_template.txt"
            }
        )

        logger.info("Prompt generated successfully")
        return prompt_data

    def _format_game_data(self, games: List[Game], config: PromptConfig) -> str:
        """Format game data for the prompt."""
        if not games:
            return "No games available"

        formatted_games = []

        for idx, game in enumerate(games, 1):
            game_str = f"\n[Game {idx}] {game.sport}\n"  # Already string
            game_str += f"Matchup: {game.away_team} @ {game.home_team}\n"

            if game.game_time:
                user_timezone = self.config.get_setting("timezone", "America/New_York")
                time_formatted = format_game_time(game.game_time, user_timezone, "%Y-%m-%d %I:%M %p %Z")
                game_str += f"Time: {time_formatted}\n"

            if game.venue:
                game_str += f"Venue: {game.venue}\n"

            # Add team stats if enabled and available
            if config.include_stats:
                if game.home_stats:
                    game_str += f"\n{game.home_team} Stats:\n"
                    game_str += self._format_team_stats(game.home_stats)

                if game.away_stats:
                    game_str += f"\n{game.away_team} Stats:\n"
                    game_str += self._format_team_stats(game.away_stats)

            # Add weather if enabled and available
            if config.include_weather and game.weather:
                game_str += f"\nWeather: {game.weather}\n"

            # Add injuries if enabled
            if config.include_injuries:
                injuries = []
                if game.home_stats and game.home_stats.injuries:
                    injuries.extend([f"{game.home_team}: {inj}" for inj in game.home_stats.injuries])
                if game.away_stats and game.away_stats.injuries:
                    injuries.extend([f"{game.away_team}: {inj}" for inj in game.away_stats.injuries])

                if injuries:
                    game_str += f"\nInjury Report:\n"
                    for injury in injuries:
                        game_str += f"  - {injury}\n"

            if game.notes:
                game_str += f"\nNotes: {game.notes}\n"

            formatted_games.append(game_str)

        return "\n".join(formatted_games)

    def _format_team_stats(self, stats) -> str:
        """Format team statistics."""
        lines = []

        if stats.wins is not None and stats.losses is not None:
            lines.append(f"  Record: {stats.wins}-{stats.losses}")

        if stats.points_per_game:
            lines.append(f"  PPG: {stats.points_per_game:.1f}")

        if stats.points_allowed_per_game:
            lines.append(f"  Opp PPG: {stats.points_allowed_per_game:.1f}")

        if stats.streak:
            lines.append(f"  Streak: {stats.streak}")

        if stats.recent_form:
            lines.append(f"  Form: {stats.recent_form}")

        return "\n".join(lines) + "\n"

    def _format_odds_data(self, games: List[Game], selected_sportsbooks: List[str] = None) -> str:
        """Format odds data for the prompt with optional sportsbook filtering."""
        if not games:
            return "No odds data available"

        formatted_odds = []

        for idx, game in enumerate(games, 1):
            if not game.odds:
                continue

            odds_str = f"\n[Game {idx}] {game.away_team} @ {game.home_team}\n"

            # Filter odds by selected sportsbooks if specified
            filtered_odds = game.odds
            if selected_sportsbooks:
                filtered_odds = [odd for odd in game.odds if odd.sportsbook in selected_sportsbooks]

            # Group odds by bet type
            odds_by_type: Dict[BetType, List] = {}
            for odd in filtered_odds:
                if odd.bet_type not in odds_by_type:
                    odds_by_type[odd.bet_type] = []
                odds_by_type[odd.bet_type].append(odd)

            # Format each bet type
            for bet_type, odds_list in odds_by_type.items():
                odds_str += f"\n  {bet_type.upper()}:\n"  # Already string

                # Group by sportsbook
                by_sportsbook: Dict[str, List] = {}
                for odd in odds_list:
                    if odd.sportsbook not in by_sportsbook:
                        by_sportsbook[odd.sportsbook] = []
                    by_sportsbook[odd.sportsbook].append(odd)

                for sportsbook, book_odds in by_sportsbook.items():
                    odds_str += f"    {sportsbook}:\n"
                    for odd in book_odds:
                        line_info = f" ({odd.line})" if odd.line else ""

                        # Calculate and add implied probability
                        implied_prob = calculate_implied_probability(odd.odds)
                        prob_str = f" [Implied: {implied_prob:.1f}%]" if implied_prob is not None else ""

                        odds_str += f"      {odd.odds}{line_info}{prob_str}\n"

            formatted_odds.append(odds_str)

        return "\n".join(formatted_odds)

    def _build_constraints(self, config: PromptConfig) -> str:
        """Build additional constraints section."""
        constraints = []

        if config.include_stats:
            constraints.append("- Consider team and player statistics")

        if config.include_injuries:
            constraints.append("- Factor in injury reports")

        if config.include_weather:
            constraints.append("- Account for weather conditions")

        if config.include_trends:
            constraints.append("- Analyze recent trends and patterns")

        # Add analysis type specific constraints
        if AnalysisType.VALUE_BETTING in config.analysis_types:
            constraints.append("- Focus on identifying +EV opportunities")

        if AnalysisType.RISK_ASSESSMENT in config.analysis_types:
            constraints.append("- Provide detailed risk analysis for each bet")

        if AnalysisType.STATISTICAL_PREDICTIONS in config.analysis_types:
            constraints.append("- Use statistical models for predictions")

        # Add parlay legs constraint if parlay is enabled
        if BetType.PARLAY in config.bet_types:
            if config.min_parlay_legs == config.max_parlay_legs:
                constraints.append(f"- Parlays must contain exactly {config.min_parlay_legs} legs")
            else:
                constraints.append(f"- Parlays must contain between {config.min_parlay_legs} and {config.max_parlay_legs} legs")

        return "\n".join(constraints) if constraints else "- None"

    def _build_contextual_factors(self, config: PromptConfig) -> str:
        """Build contextual factors list for statistical analysis section."""
        factors = []

        if config.include_stats:
            factors.append("team/player statistics")

        if config.include_injuries:
            factors.append("injuries")

        if config.include_weather:
            factors.append("weather")

        if config.include_trends:
            factors.append("recent trends")

        if factors:
            factors_str = ", ".join(factors)
            return f"   - Factor in {factors_str}"
        else:
            return ""

    def _build_analysis_sections(self, config: PromptConfig) -> str:
        """Build dynamic analysis sections based on selected analysis types."""
        sections = []
        section_num = 1

        # Parlay guidance (conditional based on bet types)
        parlay_guidance = ""
        if BetType.PARLAY in config.bet_types:
            if config.min_parlay_legs == config.max_parlay_legs:
                parlay_guidance = f"\n   - Assess correlation risk for parlays (exactly {config.min_parlay_legs} legs)"
            else:
                parlay_guidance = f"\n   - Assess correlation risk for parlays ({config.min_parlay_legs}-{config.max_parlay_legs} legs)"

        # VALUE BETTING section
        if AnalysisType.VALUE_BETTING in config.analysis_types:
            sections.append(f"""{section_num}. VALUE BETTING ASSESSMENT:
   - Identify which bets offer positive expected value
   - Compare odds across different sportsbooks
   - Highlight any significant line movements or discrepancies
   - Assess if the odds accurately reflect the true probability""")
            section_num += 1

        # RISK EVALUATION section
        if AnalysisType.RISK_ASSESSMENT in config.analysis_types:
            sections.append(f"""{section_num}. RISK EVALUATION:
   - Evaluate the risk level of each bet (Low/Medium/High)
   - Identify potential pitfalls or concerns
   - Consider variance and bankroll management{parlay_guidance}""")
            section_num += 1

        # STATISTICAL ANALYSIS section
        if AnalysisType.STATISTICAL_PREDICTIONS in config.analysis_types:
            contextual_factors = self._build_contextual_factors(config)
            sections.append(f"""{section_num}. STATISTICAL ANALYSIS:
   - Analyze team/player statistics and trends
   - Consider recent form and head-to-head history
{contextual_factors}
   - Calculate implied probability from odds""")
            section_num += 1

        # TREND ANALYSIS section (if selected separately)
        if AnalysisType.TREND_ANALYSIS in config.analysis_types:
            sections.append(f"""{section_num}. TREND ANALYSIS:
   - Identify momentum and recent performance patterns
   - Analyze home/away splits and situational trends
   - Consider rest days, travel, and scheduling factors
   - Evaluate how teams perform against similar opponents""")
            section_num += 1

        # INJURY IMPACT section (if selected separately)
        if AnalysisType.INJURY_IMPACT in config.analysis_types:
            sections.append(f"""{section_num}. INJURY IMPACT ANALYSIS:
   - Assess the significance of each injury to team performance
   - Evaluate depth chart and replacement player capabilities
   - Consider impact on game plan and strategy
   - Analyze historical performance without injured players""")
            section_num += 1

        # RECOMMENDATIONS section (always included)
        sections.append(f"""{section_num}. RECOMMENDATIONS:
   - Rank the betting opportunities by confidence level
   - Suggest optimal bet sizing for each selection
   - Provide reasoning for each recommendation
   - Highlight which bets to avoid and why""")

        return "\n\n".join(sections)

    def calculate_parlay_odds(self, selections: List[str]) -> str:
        """
        Calculate combined parlay odds from American odds.

        Args:
            selections: List of American odds strings (e.g., ["+150", "-200", "+300"])

        Returns:
            Combined odds as string
        """
        if not selections:
            return "+100"

        decimal_odds = []
        for odd_str in selections:
            try:
                odd_str = odd_str.strip().replace("+", "")
                odd = int(odd_str)

                # Convert American to decimal
                if odd > 0:
                    decimal = 1 + (odd / 100)
                else:
                    decimal = 1 + (100 / abs(odd))

                decimal_odds.append(decimal)
            except:
                logger.warning(f"Invalid odds format: {odd_str}")
                continue

        if not decimal_odds:
            return "+100"

        # Calculate combined decimal odds
        combined_decimal = 1
        for dec in decimal_odds:
            combined_decimal *= dec

        # Convert back to American
        if combined_decimal >= 2:
            combined_american = int((combined_decimal - 1) * 100)
            return f"+{combined_american}"
        else:
            combined_american = int(-100 / (combined_decimal - 1))
            return str(combined_american)

    def save_prompt(self, prompt_data: PromptData, filename: Optional[str] = None) -> Path:
        """Save generated prompt to file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            sports_str = "_".join([s.replace(" ", "") for s in prompt_data.config.sports[:2]])  # Already strings
            filename = f"prompt_{sports_str}_{timestamp}.txt"

        filepath = self.config.PROMPTS_DIR / filename

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(prompt_data.prompt_text)

            logger.info(f"Prompt saved to: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Error saving prompt: {e}")
            raise


# Singleton instance
_prompt_builder: Optional[PromptBuilder] = None


def get_prompt_builder() -> PromptBuilder:
    """Get the prompt builder singleton."""
    global _prompt_builder
    if _prompt_builder is None:
        _prompt_builder = PromptBuilder()
    return _prompt_builder
