"""
Game Selection Tab - Fetch and select live games from sportsbooks.
"""

import customtkinter as ctk
from typing import Dict, List
from datetime import datetime
import logging
from concurrent.futures import ThreadPoolExecutor, Future

from app.core.models import Game, SportType
from app.core.data_fetcher import get_odds_api_client
from app.core.odds_utils import get_odds_summary, format_game_summary
from app.core.config import get_config
from app.core.timezone_utils import format_game_time
from app.core.session_state import get_session_state
from app.ui.styles import (
    COLORS, FONTS, SPACING, DIMENSIONS,
    get_theme_colors, get_frame_style, get_button_style
)

logger = logging.getLogger(__name__)


class GameCard(ctk.CTkFrame):
    """Individual game card with selection checkbox."""

    def __init__(self, parent, game: Game, on_select_callback, **kwargs):
        super().__init__(parent, **kwargs)

        self.game = game
        self.on_select = on_select_callback
        self.config = get_config()
        self.theme = self.config.get_setting("theme", "dark")
        self.colors = get_theme_colors(self.theme)

        # Selection variable
        self.selected_var = ctk.BooleanVar(value=False)

        # Create card UI
        self._create_ui()

    def _create_ui(self):
        """Create the game card UI."""
        self.configure(**get_frame_style("card", self.theme))

        # Configure grid
        self.grid_columnconfigure(1, weight=1)

        # Checkbox
        self.checkbox = ctk.CTkCheckBox(
            self,
            text="",
            variable=self.selected_var,
            width=24,
            fg_color=self.colors["accent"],
            command=self._on_toggle
        )
        self.checkbox.grid(row=0, column=0, padx=SPACING["md"], pady=SPACING["md"], sticky="n")

        # Game info frame
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.grid(row=0, column=1, padx=SPACING["sm"], pady=SPACING["md"], sticky="ew")
        info_frame.grid_columnconfigure(0, weight=1)

        # Matchup
        matchup = ctk.CTkLabel(
            info_frame,
            text=f"{self.game.away_team} @ {self.game.home_team}",
            font=FONTS["body_large"],
            text_color=self.colors["text_primary"],
            anchor="w"
        )
        matchup.grid(row=0, column=0, sticky="w")

        # Sport badge
        sport_badge = ctk.CTkLabel(
            info_frame,
            text=f"  {self.game.sport}  ",
            font=FONTS["body_small"],
            text_color=self.colors["text_primary"],
            fg_color=self.colors["accent"],
            corner_radius=4
        )
        sport_badge.grid(row=0, column=1, padx=SPACING["sm"], sticky="e")

        # Time and venue
        # Get configured timezone
        user_timezone = self.config.get_setting("timezone", "America/New_York")
        time_str = format_game_time(self.game.game_time, user_timezone)
        venue_str = self.game.venue if self.game.venue else ""

        time_venue_text = time_str
        if venue_str:
            time_venue_text += f" • {venue_str}"

        time_venue = ctk.CTkLabel(
            info_frame,
            text=time_venue_text,
            font=FONTS["body_small"],
            text_color=self.colors["text_secondary"],
            anchor="w"
        )
        time_venue.grid(row=1, column=0, columnspan=2, sticky="w", pady=(SPACING["xs"], 0))

        # Odds summary
        summary = get_odds_summary(self.game)
        odds_text = f"{summary['total_odds']} odds • {summary['sportsbook_count']} sportsbooks • {summary['bet_type_count']} bet types"

        odds_label = ctk.CTkLabel(
            info_frame,
            text=odds_text,
            font=FONTS["body_small"],
            text_color=self.colors["success"],
            anchor="w"
        )
        odds_label.grid(row=2, column=0, columnspan=2, sticky="w", pady=(SPACING["xs"], 0))

    def _on_toggle(self):
        """Handle checkbox toggle."""
        self.on_select(self.game, self.selected_var.get())

    def get_selected(self) -> bool:
        """Check if this game is selected."""
        return self.selected_var.get()

    def set_selected(self, selected: bool):
        """Set selection state."""
        self.selected_var.set(selected)


class GameSelectionTab(ctk.CTkScrollableFrame):
    """Tab for fetching and selecting live games."""

    def __init__(self, parent, on_selection_change=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.config = get_config()
        self.theme = self.config.get_setting("theme", "dark")
        self.colors = get_theme_colors(self.theme)

        # Callback for selection changes (for undo/redo)
        self.on_selection_change = on_selection_change

        # State
        self.fetched_games: Dict[SportType, List[Game]] = {}
        self.selected_games: List[Game] = []  # Changed from Set to List (Game not hashable)
        self.selected_game_keys: set = set()  # Track unique keys to prevent duplicates
        self.game_cards: List[GameCard] = []
        self.is_loading = False

        # Filter state
        self.search_filter = ""  # Search text for filtering games

        # Thread pool for background operations (max 1 concurrent fetch)
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="GameFetch")
        self.current_fetch_future: Future = None

        # Create UI
        self._create_ui()

    def _create_ui(self):
        """Create the game selection UI."""
        self.grid_columnconfigure(0, weight=1)

        # Header
        header_frame = ctk.CTkFrame(self, **get_frame_style("card", self.theme))
        header_frame.grid(row=0, column=0, padx=SPACING["xl"], pady=(SPACING["xl"], SPACING["md"]), sticky="ew")
        header_frame.grid_columnconfigure(1, weight=1)

        # Title
        title = ctk.CTkLabel(
            header_frame,
            text="📋 Live Games",
            font=FONTS["heading_medium"],
            text_color=self.colors["text_primary"]
        )
        title.grid(row=0, column=0, padx=SPACING["lg"], pady=SPACING["lg"], sticky="w")

        # Button frame
        btn_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        btn_frame.grid(row=0, column=2, padx=SPACING["lg"], pady=SPACING["lg"], sticky="e")

        # Fetch Games button
        self.fetch_btn = ctk.CTkButton(
            btn_frame,
            text="🔄 Fetch Games",
            font=FONTS["body_medium"],
            **get_button_style("primary", self.theme),
            width=140,
            height=DIMENSIONS["button_height"],
            command=self._fetch_games
        )
        self.fetch_btn.grid(row=0, column=0, padx=SPACING["sm"])

        # Select All button
        self.select_all_btn = ctk.CTkButton(
            btn_frame,
            text="Select All",
            font=FONTS["body_medium"],
            **get_button_style("secondary", self.theme),
            width=100,
            height=DIMENSIONS["button_height"],
            command=self._select_all
        )
        self.select_all_btn.grid(row=0, column=1, padx=SPACING["sm"])

        # Clear button
        self.clear_btn = ctk.CTkButton(
            btn_frame,
            text="Clear",
            font=FONTS["body_medium"],
            **get_button_style("secondary", self.theme),
            width=80,
            height=DIMENSIONS["button_height"],
            command=self._clear_all
        )
        self.clear_btn.grid(row=0, column=2, padx=SPACING["sm"])

        # Status/Info row
        info_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        info_frame.grid(row=1, column=0, columnspan=3, padx=SPACING["lg"], pady=(0, SPACING["lg"]), sticky="ew")

        self.status_label = ctk.CTkLabel(
            info_frame,
            text="Select sports in the Sports tab, then click 'Fetch Games'",
            font=FONTS["body_small"],
            text_color=self.colors["text_secondary"]
        )
        self.status_label.grid(row=0, column=0, sticky="w")

        self.selection_count_label = ctk.CTkLabel(
            info_frame,
            text="0 games selected",
            font=FONTS["body_small"],
            text_color=self.colors["accent"]
        )
        self.selection_count_label.grid(row=0, column=1, padx=SPACING["lg"], sticky="e")

        # Search/Filter Section
        filter_frame = ctk.CTkFrame(self, **get_frame_style("card", self.theme))
        filter_frame.grid(row=1, column=0, padx=SPACING["xl"], pady=(0, SPACING["md"]), sticky="ew")
        filter_frame.grid_columnconfigure(1, weight=1)

        # Search icon/label
        search_label = ctk.CTkLabel(
            filter_frame,
            text="🔍 Search:",
            font=FONTS["body_medium"],
            text_color=self.colors["text_primary"]
        )
        search_label.grid(row=0, column=0, padx=SPACING["lg"], pady=SPACING["md"], sticky="w")

        # Search entry
        self.search_entry = ctk.CTkEntry(
            filter_frame,
            placeholder_text="Filter by team name...",
            font=FONTS["body_medium"],
            fg_color=self.colors["bg_tertiary"],
            border_color=self.colors["accent"],
            text_color=self.colors["text_primary"],
            placeholder_text_color=self.colors["text_secondary"]
        )
        self.search_entry.grid(row=0, column=1, padx=SPACING["md"], pady=SPACING["md"], sticky="ew")
        self.search_entry.bind("<KeyRelease>", self._on_search_changed)

        # Clear search button
        clear_search_btn = ctk.CTkButton(
            filter_frame,
            text="✕",
            font=FONTS["body_medium"],
            **get_button_style("secondary", self.theme),
            width=40,
            height=DIMENSIONS["button_height"],
            command=self._clear_search
        )
        clear_search_btn.grid(row=0, column=2, padx=SPACING["lg"], pady=SPACING["md"])

        # Games container
        self.games_container = ctk.CTkFrame(self, fg_color="transparent")
        self.games_container.grid(row=2, column=0, padx=SPACING["xl"], pady=SPACING["md"], sticky="ew")
        self.games_container.grid_columnconfigure(0, weight=1)

    def _fetch_games(self):
        """Fetch games from The Odds API."""
        if self.is_loading:
            logger.info("Already fetching games, please wait...")
            return

        # Get selected sports from parent app
        try:
            from app.ui.app_window import PromptBuilderApp
            app = self.winfo_toplevel()

            if hasattr(app, 'tabs') and "Sports" in app.tabs:
                sports_tab = app.tabs["Sports"]
                selected_sports = sports_tab.get_selected_sports()

                if not selected_sports:
                    self._update_status("Please select at least one sport first", "error")
                    return

                # Cancel any existing fetch operation
                if self.current_fetch_future and not self.current_fetch_future.done():
                    self.current_fetch_future.cancel()
                    logger.info("Cancelled previous fetch operation")

                # Get selected bet types from Bet Config tab
                selected_bet_types = None
                if "Bet Config" in app.tabs:
                    bet_config_tab = app.tabs["Bet Config"]
                    bet_config = bet_config_tab.get_configuration()
                    selected_bet_types = bet_config.get("bet_types", [])

                    if selected_bet_types:
                        logger.info(f"Using {len(selected_bet_types)} selected bet types")

                # Start loading
                self.is_loading = True
                self.fetch_btn.configure(text="⏳ Fetching...", state="disabled")
                self._update_status(f"Fetching games for {len(selected_sports)} sports...", "loading")

                # Fetch in background using thread pool
                def fetch_task():
                    """Background task to fetch games from API."""
                    client = get_odds_api_client()
                    # Pass bet_types so they can be filtered per-sport
                    return client.get_games_with_odds(selected_sports, bet_types=selected_bet_types)

                # Submit task and store future
                self.current_fetch_future = self.executor.submit(fetch_task)

                # Add callback to handle completion (avoids lambda capture)
                self.current_fetch_future.add_done_callback(self._on_fetch_complete)

            else:
                self._update_status("Cannot access Sports tab", "error")

        except Exception as e:
            logger.error(f"Error fetching games: {e}")
            self._update_status(f"Error: {str(e)}", "error")
            self.is_loading = False
            self.fetch_btn.configure(text="🔄 Fetch Games", state="normal")

    def _on_fetch_complete(self, future: Future):
        """
        Handle completion of fetch task (called from background thread).

        This callback is executed in the background thread, so all UI updates
        must be scheduled on the main thread using self.after().
        """
        try:
            # Get the result (raises exception if task failed)
            games_dict = future.result()

            # Schedule UI update on main thread
            self.after(0, self._on_games_fetched, games_dict)

        except Exception as e:
            # Schedule error handling on main thread
            error_msg = str(e)
            self.after(0, self._on_fetch_error, error_msg)

    def _on_games_fetched(self, games_dict: Dict[SportType, List[Game]]):
        """Handle successful games fetch (runs on main thread)."""
        self.fetched_games = games_dict
        self.is_loading = False
        self.fetch_btn.configure(text="🔄 Fetch Games", state="normal")

        # Count total games
        total_games = sum(len(games) for games in games_dict.values())

        if total_games == 0:
            self._update_status("No games found for selected sports", "warning")
            return

        # Display games
        self._display_games()

        # Restore previous selections from session
        self._restore_session_state()

        # Update status
        self._update_status(f"✓ Fetched {total_games} games", "success")
        logger.info(f"Successfully fetched {total_games} games")

    def _on_fetch_error(self, error: str):
        """Handle fetch error (runs on main thread)."""
        self.is_loading = False
        self.fetch_btn.configure(text="🔄 Fetch Games", state="normal")
        self._update_status(f"Error: {error}", "error")
        logger.error(f"Failed to fetch games: {error}")

    def _display_games(self):
        """Display fetched games as cards, filtered by search criteria."""
        # Clear existing cards
        for card in self.game_cards:
            card.destroy()
        self.game_cards.clear()

        # Create new cards
        row = 0
        total_shown = 0
        for sport, games in self.fetched_games.items():
            if not games:
                continue

            # Filter games based on search criteria
            filtered_games = [game for game in games if self._game_matches_filter(game)]

            if not filtered_games:
                continue  # Skip sport if no games match filter

            # Sport header with filtered count
            header_text = f"━━━ {sport} ({len(filtered_games)} games"
            if len(filtered_games) < len(games):
                header_text += f" of {len(games)}"
            header_text += ") ━━━"

            sport_header = ctk.CTkLabel(
                self.games_container,
                text=header_text,
                font=FONTS["heading_small"],
                text_color=self.colors["accent"]
            )
            sport_header.grid(row=row, column=0, pady=(SPACING["lg"], SPACING["md"]), sticky="w")
            row += 1

            # Game cards (only filtered games)
            for game in filtered_games:
                card = GameCard(
                    self.games_container,
                    game,
                    self._on_game_selected,
                    fg_color=self.colors["bg_secondary"]
                )
                card.grid(row=row, column=0, pady=SPACING["sm"], sticky="ew")
                self.game_cards.append(card)
                row += 1
                total_shown += 1

        # Update status if filtering
        if self.search_filter:
            total_games = sum(len(games) for games in self.fetched_games.values())
            if total_shown < total_games:
                self._update_status(f"Showing {total_shown} of {total_games} games", "info")

    def _game_matches_filter(self, game: Game) -> bool:
        """
        Check if a game matches the current search filter.

        Args:
            game: Game to check

        Returns:
            bool: True if game matches filter (or no filter active), False otherwise
        """
        # If no filter, show all games
        if not self.search_filter:
            return True

        # Case-insensitive search
        search_lower = self.search_filter.lower()

        # Check team names
        if search_lower in game.home_team.lower():
            return True
        if search_lower in game.away_team.lower():
            return True

        # Check sport
        if search_lower in str(game.sport).lower():
            return True

        # Check venue
        if game.venue and search_lower in game.venue.lower():
            return True

        return False

    def _on_search_changed(self, event=None):
        """Handle search text change."""
        self.search_filter = self.search_entry.get().strip()
        # Redisplay games with filter applied
        self._display_games()
        logger.debug(f"Search filter updated: '{self.search_filter}'")

    def _clear_search(self):
        """Clear the search filter."""
        self.search_entry.delete(0, 'end')
        self.search_filter = ""
        self._display_games()
        logger.debug("Search filter cleared")

    def _on_game_selected(self, game: Game, selected: bool):
        """Handle game selection change."""
        # Capture old state for undo/redo
        old_state = list(self.selected_games)

        game_key = game.get_unique_key()

        if selected:
            if game_key not in self.selected_game_keys:
                self.selected_games.append(game)
                self.selected_game_keys.add(game_key)
        else:
            if game_key in self.selected_game_keys:
                # Remove game by finding it with matching key
                self.selected_games = [g for g in self.selected_games if g.get_unique_key() != game_key]
                self.selected_game_keys.remove(game_key)

        self._update_selection_count()
        self._save_session_state()
        logger.debug(f"Game {'selected' if selected else 'deselected'}: {format_game_summary(game)}")

        # Record change for undo/redo
        if self.on_selection_change:
            new_state = list(self.selected_games)
            self.on_selection_change(old_state, new_state)

    def _save_session_state(self):
        """Save current selections to session state."""
        session = get_session_state()
        session.set("selected_game_keys", list(self.selected_game_keys))

    def _restore_session_state(self):
        """Restore selections from session state."""
        session = get_session_state()
        saved_keys = session.get("selected_game_keys", [])

        if not saved_keys:
            return

        # Restore selections for games that were previously selected
        restored_count = 0
        for card in self.game_cards:
            game_key = card.game.get_unique_key()
            if game_key in saved_keys:
                card.set_selected(True)
                if game_key not in self.selected_game_keys:
                    self.selected_games.append(card.game)
                    self.selected_game_keys.add(game_key)
                    restored_count += 1

        if restored_count > 0:
            self._update_selection_count()
            logger.info(f"Restored {restored_count} game selections from session")

    def _select_all(self):
        """Select all fetched games."""
        for card in self.game_cards:
            card.set_selected(True)
            game_key = card.game.get_unique_key()
            if game_key not in self.selected_game_keys:
                self.selected_games.append(card.game)
                self.selected_game_keys.add(game_key)

        self._update_selection_count()
        self._save_session_state()
        logger.info(f"Selected all {len(self.game_cards)} games")

    def _clear_all(self):
        """Clear all selections."""
        for card in self.game_cards:
            card.set_selected(False)

        self.selected_games.clear()
        self.selected_game_keys.clear()
        self._update_selection_count()
        self._save_session_state()
        logger.info("Cleared all game selections")

    def _update_selection_count(self):
        """Update the selection count label."""
        count = len(self.selected_games)
        plural = "s" if count != 1 else ""
        self.selection_count_label.configure(text=f"{count} game{plural} selected")

    def _update_status(self, message: str, status_type: str = "info"):
        """Update status label."""
        color_map = {
            "success": self.colors["success"],
            "error": self.colors["error"],
            "warning": self.colors["warning"],
            "loading": self.colors["accent"],
            "info": self.colors["text_secondary"]
        }

        self.status_label.configure(
            text=message,
            text_color=color_map.get(status_type, self.colors["text_secondary"])
        )

    def get_selected_games(self) -> List[Game]:
        """Get list of selected games."""
        return list(self.selected_games)

    def set_selected_games(self, games: List[Game]):
        """
        Set selected games programmatically (for undo/redo).

        Args:
            games: List of games to select
        """
        # Clear current selections
        self.selected_games.clear()
        self.selected_game_keys.clear()

        # Update game cards to reflect new selection
        for card in self.game_cards:
            card.set_selected(False)

        # Set new selections
        for game in games:
            game_key = self._get_game_key(game)
            if game_key not in self.selected_game_keys:
                self.selected_game_keys.add(game_key)
                self.selected_games.append(game)

                # Update corresponding card if it exists
                for card in self.game_cards:
                    if self._get_game_key(card.game) == game_key:
                        card.set_selected(True)
                        break

        # Update selection count
        self._update_selection_count()

        # Save to session
        self._save_session_state()

        logger.info(f"Set selected games: {len(games)} games")

    def get_all_games(self) -> List[Game]:
        """Get all fetched games."""
        all_games = []
        for games in self.fetched_games.values():
            all_games.extend(games)
        return all_games

    def destroy(self):
        """Clean up resources before destroying the widget."""
        # Cancel any pending fetch operations
        if self.current_fetch_future and not self.current_fetch_future.done():
            self.current_fetch_future.cancel()
            logger.info("Cancelled pending fetch operation during cleanup")

        # Shutdown the thread pool executor
        self.executor.shutdown(wait=False)
        logger.info("Thread pool executor shut down")

        # Call parent destroy
        super().destroy()
