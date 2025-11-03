"""
Odds Review Tab - Display and review odds grouped by bet type.
"""

import customtkinter as ctk
from typing import List, Dict
import logging

from app.core.models import Game, BetType, OddsData, BET_TYPE_DISPLAY_NAMES, MarketCategory, MARKET_GROUPS
from app.core.odds_utils import (
    group_odds_by_bet_type,
    compare_odds_across_sportsbooks,
    find_best_odds,
    format_odds_for_display,
    get_odds_summary
)
from app.core.config import get_config
from app.core.timezone_utils import format_game_time
from app.ui.styles import (
    COLORS, FONTS, SPACING, DIMENSIONS,
    get_theme_colors, get_frame_style
)

logger = logging.getLogger(__name__)


class BetTypeSection(ctk.CTkFrame):
    """Collapsible section for a single bet type."""

    def __init__(self, parent, bet_type: str, odds_list: List[OddsData], **kwargs):
        super().__init__(parent, **kwargs)

        self.bet_type = bet_type
        self.odds_list = odds_list
        self.config = get_config()
        self.theme = self.config.get_setting("theme", "dark")
        self.colors = get_theme_colors(self.theme)

        self.is_expanded = True

        # Create UI
        self._create_ui()

    def _create_ui(self):
        """Create the bet type section UI."""
        self.configure(**get_frame_style("card", self.theme))
        self.grid_columnconfigure(0, weight=1)

        # Header with toggle
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=SPACING["md"], pady=SPACING["md"], sticky="ew")
        header_frame.grid_columnconfigure(1, weight=1)

        # Get friendly display name and category icon
        display_name = self._get_display_name()
        icon = self._get_market_icon()

        # Bet type icon and name
        bet_type_label = ctk.CTkLabel(
            header_frame,
            text=f"{icon} {display_name}",
            font=FONTS["heading_small"],
            text_color=self.colors["accent"],
            anchor="w"
        )
        bet_type_label.grid(row=0, column=0, sticky="w")

        # Odds count
        count_label = ctk.CTkLabel(
            header_frame,
            text=f"{len(self.odds_list)} odds",
            font=FONTS["body_small"],
            text_color=self.colors["text_secondary"]
        )
        count_label.grid(row=0, column=1, padx=SPACING["md"], sticky="e")

        # Odds display area
        self.odds_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.odds_frame.grid(row=1, column=0, padx=SPACING["lg"], pady=(0, SPACING["md"]), sticky="ew")
        self.odds_frame.grid_columnconfigure(1, weight=1)

        # Group odds by sportsbook
        by_sportsbook = {}
        for odd in self.odds_list:
            if odd.sportsbook not in by_sportsbook:
                by_sportsbook[odd.sportsbook] = []
            by_sportsbook[odd.sportsbook].append(odd)

        # Display odds by sportsbook
        row = 0
        for sportsbook, sportsbook_odds in sorted(by_sportsbook.items()):
            # Sportsbook name
            book_label = ctk.CTkLabel(
                self.odds_frame,
                text=sportsbook,
                font=FONTS["body_medium"],
                text_color=self.colors["text_primary"],
                anchor="w",
                width=120
            )
            book_label.grid(row=row, column=0, sticky="w", pady=SPACING["xs"])

            # Odds values
            odds_text = " • ".join([format_odds_for_display(odd) for odd in sportsbook_odds])
            odds_label = ctk.CTkLabel(
                self.odds_frame,
                text=odds_text,
                font=FONTS["mono_small"],
                text_color=self.colors["success"],
                anchor="w"
            )
            odds_label.grid(row=row, column=1, sticky="w", padx=SPACING["md"], pady=SPACING["xs"])

            row += 1

    def _get_display_name(self) -> str:
        """Get friendly display name for this bet type."""
        # Try to match bet_type string to BetType enum
        try:
            # Convert string to BetType enum (bet_type is stored as string in grouped_odds)
            bet_type_enum = BetType(self.bet_type)
            return BET_TYPE_DISPLAY_NAMES.get(bet_type_enum, self.bet_type.upper())
        except (ValueError, KeyError):
            return self.bet_type.upper()

    def _get_market_icon(self) -> str:
        """Get icon for this market type based on category."""
        try:
            bet_type_enum = BetType(self.bet_type)

            # Check which category this bet type belongs to
            for category, bet_types in MARKET_GROUPS.items():
                if bet_type_enum in bet_types:
                    category_icons = {
                        MarketCategory.BASIC: "📊",
                        MarketCategory.ALTERNATE_LINES: "↕️",
                        MarketCategory.PERIOD: "🕐",
                        MarketCategory.SOCCER: "⚽",
                        MarketCategory.PLAYER_PROPS_NFL: "🏈",
                        MarketCategory.PLAYER_PROPS_NBA: "🏀",
                        MarketCategory.PLAYER_PROPS_MLB: "⚾",
                        MarketCategory.PLAYER_PROPS_NHL: "🏒",
                    }
                    return category_icons.get(category, "📌")

            return "📊"  # Default
        except (ValueError, KeyError):
            return "📊"


class GameOddsPanel(ctk.CTkFrame):
    """Panel displaying all odds for a single game."""

    def __init__(self, parent, game: Game, **kwargs):
        super().__init__(parent, **kwargs)

        self.game = game
        self.config = get_config()
        self.theme = self.config.get_setting("theme", "dark")
        self.colors = get_theme_colors(self.theme)

        # Create UI
        self._create_ui()

    def _create_ui(self):
        """Create the game odds panel UI."""
        self.configure(**get_frame_style("card", self.theme))
        self.grid_columnconfigure(0, weight=1)

        # Game header
        header_frame = ctk.CTkFrame(self, fg_color=self.colors["bg_tertiary"], corner_radius=6)
        header_frame.grid(row=0, column=0, padx=SPACING["md"], pady=SPACING["md"], sticky="ew")
        header_frame.grid_columnconfigure(1, weight=1)

        # Matchup
        matchup_label = ctk.CTkLabel(
            header_frame,
            text=f"{self.game.away_team} @ {self.game.home_team}",
            font=FONTS["heading_small"],
            text_color=self.colors["text_primary"],
            anchor="w"
        )
        matchup_label.grid(row=0, column=0, padx=SPACING["lg"], pady=SPACING["md"], sticky="w")

        # Sport badge
        sport_badge = ctk.CTkLabel(
            header_frame,
            text=f"  {self.game.sport}  ",
            font=FONTS["body_small"],
            text_color=self.colors["text_primary"],
            fg_color=self.colors["accent"],
            corner_radius=4
        )
        sport_badge.grid(row=0, column=1, padx=SPACING["lg"], pady=SPACING["md"], sticky="e")

        # Game details
        details_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        details_frame.grid(row=1, column=0, columnspan=2, padx=SPACING["lg"], pady=(0, SPACING["md"]), sticky="ew")

        # Time
        user_timezone = self.config.get_setting("timezone", "America/New_York")
        time_str = format_game_time(self.game.game_time, user_timezone, "%a, %b %d at %I:%M %p %Z")
        time_label = ctk.CTkLabel(
            details_frame,
            text=f"🕐 {time_str}",
            font=FONTS["body_small"],
            text_color=self.colors["text_secondary"],
            anchor="w"
        )
        time_label.grid(row=0, column=0, sticky="w")

        # Venue
        if self.game.venue:
            venue_label = ctk.CTkLabel(
                details_frame,
                text=f"📍 {self.game.venue}",
                font=FONTS["body_small"],
                text_color=self.colors["text_secondary"],
                anchor="w"
            )
            venue_label.grid(row=0, column=1, padx=SPACING["xl"], sticky="w")

        # Odds summary
        summary = get_odds_summary(self.game)
        summary_text = f"💰 {summary['total_odds']} total odds from {summary['sportsbook_count']} sportsbooks"
        summary_label = ctk.CTkLabel(
            details_frame,
            text=summary_text,
            font=FONTS["body_small"],
            text_color=self.colors["success"],
            anchor="w"
        )
        summary_label.grid(row=1, column=0, columnspan=2, pady=(SPACING["xs"], 0), sticky="w")

        # Group odds by bet type
        grouped_odds = group_odds_by_bet_type(self.game)

        # Display each bet type
        row = 1
        for bet_type, odds_list in sorted(grouped_odds.items()):
            bet_section = BetTypeSection(
                self,
                bet_type,
                odds_list,
                fg_color=self.colors["bg_secondary"]
            )
            bet_section.grid(row=row, column=0, padx=SPACING["md"], pady=SPACING["sm"], sticky="ew")
            row += 1


class OddsReviewTab(ctk.CTkScrollableFrame):
    """Tab for reviewing odds for selected games."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        self.config = get_config()
        self.theme = self.config.get_setting("theme", "dark")
        self.colors = get_theme_colors(self.theme)

        # State
        self.game_panels: List[GameOddsPanel] = []

        # Create UI
        self._create_ui()

    def _create_ui(self):
        """Create the odds review UI."""
        self.grid_columnconfigure(0, weight=1)

        # Header
        header_frame = ctk.CTkFrame(self, **get_frame_style("card", self.theme))
        header_frame.grid(row=0, column=0, padx=SPACING["xl"], pady=(SPACING["xl"], SPACING["md"]), sticky="ew")
        header_frame.grid_columnconfigure(1, weight=1)

        # Title
        title = ctk.CTkLabel(
            header_frame,
            text="📊 Odds Review",
            font=FONTS["heading_medium"],
            text_color=self.colors["text_primary"]
        )
        title.grid(row=0, column=0, padx=SPACING["lg"], pady=SPACING["lg"], sticky="w")

        # Info label
        self.info_label = ctk.CTkLabel(
            header_frame,
            text="Select games in the Games tab to review odds",
            font=FONTS["body_small"],
            text_color=self.colors["text_secondary"]
        )
        self.info_label.grid(row=1, column=0, columnspan=2, padx=SPACING["lg"], pady=(0, SPACING["lg"]), sticky="w")

        # Odds container
        self.odds_container = ctk.CTkFrame(self, fg_color="transparent")
        self.odds_container.grid(row=1, column=0, padx=SPACING["xl"], pady=SPACING["md"], sticky="ew")
        self.odds_container.grid_columnconfigure(0, weight=1)

    def load_games(self, games: List[Game], sportsbook_filter: List[str] = None):
        """Load and display odds for selected games with optional sportsbook filter."""
        # Clear existing panels
        for panel in self.game_panels:
            panel.destroy()
        self.game_panels.clear()

        if not games:
            self.info_label.configure(
                text="No games selected. Go to the Games tab to select games.",
                text_color=self.colors["warning"]
            )
            return

        # Apply sportsbook filter if specified
        filtered_games = games
        if sportsbook_filter:
            filtered_games = self._filter_games_by_sportsbooks(games, sportsbook_filter)
            filter_info = f" (filtered to {len(sportsbook_filter)} sportsbook{'s' if len(sportsbook_filter) != 1 else ''})"
        else:
            filter_info = ""

        # Update info
        self.info_label.configure(
            text=f"Reviewing odds for {len(games)} selected game{'s' if len(games) != 1 else ''}{filter_info}",
            text_color=self.colors["success"]
        )

        # Create panels for each game
        row = 0
        for game in filtered_games:
            panel = GameOddsPanel(
                self.odds_container,
                game,
                fg_color=self.colors["bg_secondary"]
            )
            panel.grid(row=row, column=0, pady=SPACING["md"], sticky="ew")
            self.game_panels.append(panel)
            row += 1

        logger.info(f"Loaded odds for {len(games)} games with sportsbook filter: {sportsbook_filter}")

    def _filter_games_by_sportsbooks(self, games: List[Game], sportsbook_filter: List[str]) -> List[Game]:
        """Filter games to only include odds from selected sportsbooks."""
        from copy import deepcopy

        filtered_games = []
        for game in games:
            # Create a copy of the game with filtered odds
            filtered_game = deepcopy(game)
            filtered_game.odds = [
                odd for odd in game.odds
                if odd.sportsbook in sportsbook_filter
            ]

            # Only include game if it has odds after filtering
            if filtered_game.odds:
                filtered_games.append(filtered_game)

        return filtered_games

    def refresh(self):
        """Refresh odds display from parent app's selected games."""
        try:
            app = self.winfo_toplevel()

            if hasattr(app, 'tabs') and "Games" in app.tabs:
                games_tab = app.tabs["Games"]
                selected_games = games_tab.get_selected_games()

                self.load_games(selected_games)
            else:
                logger.warning("Cannot access Games tab for refresh")

        except Exception as e:
            logger.error(f"Error refreshing odds: {e}")
