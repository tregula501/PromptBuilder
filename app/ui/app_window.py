"""
Main application window for PromptBuilder.
"""

import customtkinter as ctk
from typing import Optional
import logging

from app.core.config import get_config
from app.ui.styles import (
    COLORS, FONTS, SPACING, DIMENSIONS,
    get_theme_colors, get_button_style
)
from app.ui.tabs.sports_selection import SportsSelectionTab
from app.ui.tabs.game_selection import GameSelectionTab
from app.ui.tabs.odds_review import OddsReviewTab
from app.ui.tabs.bet_configuration import BetConfigurationTab
from app.ui.tabs.prompt_preview import PromptPreviewTab
from app.core.prompt_builder import get_prompt_builder
from app.core.data_fetcher import get_odds_api_client
from app.core.models import PromptConfig

logger = logging.getLogger(__name__)


class PromptBuilderApp(ctk.CTk):
    """Main application window."""

    # UI timing constants
    STATUS_RESET_TIMEOUT_MS = 3000  # Auto-reset status message after 3 seconds

    def __init__(self):
        super().__init__()

        # Load configuration
        self.config = get_config()
        self.theme = self.config.get_setting("theme", "dark")

        # Configure window
        self.title("PromptBuilder - AI Sportsbook Betting Prompt Generator")
        self.geometry("1200x800")
        self.minsize(DIMENSIONS["min_window_width"], DIMENSIONS["min_window_height"])

        # Set theme
        ctk.set_appearance_mode(self.theme)
        ctk.set_default_color_theme("blue")

        # Configure grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Create UI elements
        self._create_sidebar()
        self._create_main_content()

        # Bind keyboard shortcuts
        self._setup_keyboard_shortcuts()

        logger.info("Application window initialized")

    def _create_sidebar(self):
        """Create the sidebar with navigation."""
        colors = get_theme_colors(self.theme)

        # Sidebar frame
        self.sidebar = ctk.CTkFrame(
            self,
            width=DIMENSIONS["sidebar_width"],
            corner_radius=0,
            fg_color=colors["bg_secondary"]
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.sidebar.grid_rowconfigure(10, weight=1)

        # Logo/Title
        self.logo_label = ctk.CTkLabel(
            self.sidebar,
            text="PromptBuilder",
            font=FONTS["heading_medium"],
            text_color=colors["accent"]
        )
        self.logo_label.grid(row=0, column=0, padx=SPACING["lg"], pady=(SPACING["xl"], SPACING["lg"]))

        # Subtitle
        self.subtitle_label = ctk.CTkLabel(
            self.sidebar,
            text="AI Betting Prompt Generator",
            font=FONTS["body_small"],
            text_color=colors["text_secondary"]
        )
        self.subtitle_label.grid(row=1, column=0, padx=SPACING["lg"], pady=(0, SPACING["xl"]))

        # Navigation buttons
        self.nav_buttons = {}
        nav_items = [
            ("Sports", "🏈"),
            ("Games", "📋"),
            ("Odds", "💰"),
            ("Bet Config", "⚙️"),
            ("Preview", "👁️"),
        ]

        for idx, (label, icon) in enumerate(nav_items, start=2):
            btn = ctk.CTkButton(
                self.sidebar,
                text=f"{icon}  {label}",
                font=FONTS["body_medium"],
                **get_button_style("secondary", self.theme),
                height=DIMENSIONS["button_height"],
                anchor="w",
                command=lambda l=label: self._switch_tab(l)
            )
            btn.grid(row=idx, column=0, padx=SPACING["lg"], pady=SPACING["xs"], sticky="ew")
            self.nav_buttons[label] = btn

        # Bottom buttons
        self.generate_btn = ctk.CTkButton(
            self.sidebar,
            text="🚀 Generate Prompt",
            font=FONTS["body_medium"],
            **get_button_style("primary", self.theme),
            height=DIMENSIONS["button_height"] + 8,
            command=self._generate_prompt
        )
        self.generate_btn.grid(row=11, column=0, padx=SPACING["lg"], pady=SPACING["md"], sticky="ew")

        # Version label
        self.version_label = ctk.CTkLabel(
            self.sidebar,
            text="v1.0.0",
            font=FONTS["body_small"],
            text_color=colors["text_muted"]
        )
        self.version_label.grid(row=12, column=0, padx=SPACING["lg"], pady=(0, SPACING["md"]))

    def _create_main_content(self):
        """Create the main content area with tabs."""
        colors = get_theme_colors(self.theme)

        # Main container
        self.main_container = ctk.CTkFrame(
            self,
            corner_radius=0,
            fg_color=colors["bg_primary"]
        )
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.main_container.grid_rowconfigure(1, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        # Header
        self.header = ctk.CTkFrame(
            self.main_container,
            corner_radius=0,
            height=60,
            fg_color=colors["bg_secondary"]
        )
        self.header.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        self.header.grid_columnconfigure(1, weight=1)

        self.header_title = ctk.CTkLabel(
            self.header,
            text="Sports Selection",
            font=FONTS["heading_medium"],
            text_color=colors["text_primary"]
        )
        self.header_title.grid(row=0, column=0, padx=SPACING["xl"], pady=SPACING["lg"], sticky="w")

        # Status indicator
        self.status_label = ctk.CTkLabel(
            self.header,
            text="● Ready",
            font=FONTS["body_medium"],
            text_color=colors["success"]
        )
        self.status_label.grid(row=0, column=2, padx=SPACING["xl"], pady=SPACING["lg"], sticky="e")

        # Content area (tabbed)
        self.content_area = ctk.CTkFrame(
            self.main_container,
            corner_radius=0,
            fg_color=colors["bg_primary"]
        )
        self.content_area.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        self.content_area.grid_rowconfigure(0, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)

        # Tab frames
        self.tabs = {}
        self._create_tabs()

        # Show default tab
        self.current_tab = "Sports"
        self._switch_tab("Sports")

    def _create_tabs(self):
        """Create application tabs."""
        colors = get_theme_colors(self.theme)

        # Sports Selection Tab
        self.tabs["Sports"] = SportsSelectionTab(
            self.content_area,
            fg_color=colors["bg_primary"]
        )

        # Game Selection Tab (NEW)
        self.tabs["Games"] = GameSelectionTab(
            self.content_area,
            fg_color=colors["bg_primary"]
        )

        # Odds Review Tab (NEW)
        self.tabs["Odds"] = OddsReviewTab(
            self.content_area,
            fg_color=colors["bg_primary"]
        )

        # Bet Configuration Tab
        self.tabs["Bet Config"] = BetConfigurationTab(
            self.content_area,
            fg_color=colors["bg_primary"]
        )

        # Prompt Preview Tab
        self.tabs["Preview"] = PromptPreviewTab(
            self.content_area,
            fg_color=colors["bg_primary"]
        )

    def _switch_tab(self, tab_name: str):
        """Switch to the specified tab."""
        if tab_name not in self.tabs:
            logger.warning(f"Tab '{tab_name}' does not exist")
            return

        # Hide current tab
        if self.current_tab in self.tabs:
            self.tabs[self.current_tab].grid_remove()

        # Show new tab
        self.tabs[tab_name].grid(row=0, column=0, sticky="nsew")
        self.current_tab = tab_name

        # Special handling for Odds tab - auto-refresh with selected games
        if tab_name == "Odds":
            try:
                games_tab = self.tabs["Games"]
                selected_games = games_tab.get_selected_games()

                # Get sportsbook filter from Bet Config
                bet_tab = self.tabs["Bet Config"]
                bet_config = bet_tab.get_configuration()
                sportsbook_filter = bet_config.get("selected_sportsbooks", [])

                odds_tab = self.tabs["Odds"]
                odds_tab.load_games(selected_games, sportsbook_filter if sportsbook_filter else None)
            except Exception as e:
                logger.error(f"Error refreshing Odds tab: {e}")

        # Update header
        self.header_title.configure(text=tab_name)

        # Update nav button states
        colors = get_theme_colors(self.theme)
        for name, btn in self.nav_buttons.items():
            if name == tab_name:
                btn.configure(fg_color=colors["accent"])
            else:
                btn.configure(fg_color=colors["bg_tertiary"])

        logger.info(f"Switched to tab: {tab_name}")

    def _generate_prompt(self):
        """Generate prompt based on current configuration."""
        self._update_status("Generating prompt...", "warning")
        logger.info("Generate prompt button clicked")

        try:
            # Get selected games from Games tab
            games_tab = self.tabs["Games"]
            selected_games = games_tab.get_selected_games()

            if not selected_games:
                self._update_status("Please select games first (Games tab)", "error")
                return

            # Get selected sports (for config)
            sports_tab = self.tabs["Sports"]
            selected_sports = sports_tab.get_selected_sports()

            if not selected_sports:
                # Infer sports from selected games if not explicitly selected
                selected_sports = list(set(game.sport for game in selected_games))

            # Get bet configuration
            bet_tab = self.tabs["Bet Config"]
            bet_config = bet_tab.get_configuration()

            # Create prompt configuration
            config = PromptConfig(
                sports=selected_sports,
                max_combined_odds=bet_config["max_odds"],
                min_parlay_legs=bet_config.get("min_parlay_legs", 2),
                max_parlay_legs=bet_config.get("max_parlay_legs", 10),
                bet_types=bet_config["bet_types"],
                analysis_types=bet_config["analysis_types"],
                risk_tolerance=bet_config["risk_level"],
                include_stats=bet_config["include_stats"],
                include_injuries=bet_config["include_injuries"],
                include_weather=bet_config["include_weather"],
                include_trends=bet_config["include_trends"],
                custom_context=bet_config.get("custom_context") or None,
                selected_sportsbooks=bet_config.get("selected_sportsbooks", [])
            )

            # Build prompt with SELECTED GAMES (not empty list!)
            builder = get_prompt_builder()
            prompt_data = builder.build_prompt(config, selected_games)

            # Show in preview tab
            preview_tab = self.tabs["Preview"]
            preview_tab.set_prompt(prompt_data.prompt_text)

            # Switch to preview tab
            self._switch_tab("Preview")

            self._update_status(f"Prompt generated with {len(selected_games)} games!", "success")
            logger.info(f"Prompt generated successfully with {len(selected_games)} games")

        except Exception as e:
            self._update_status(f"Error: {str(e)}", "error")
            logger.error(f"Error generating prompt: {e}", exc_info=True)

    def _setup_keyboard_shortcuts(self):
        """Set up keyboard shortcuts for common actions."""
        # Ctrl/Cmd+G: Generate Prompt
        self.bind("<Control-g>", lambda event: self._generate_prompt())
        self.bind("<Command-g>", lambda event: self._generate_prompt())  # macOS

        # Ctrl/Cmd+S: Save Prompt (when in Preview tab)
        self.bind("<Control-s>", lambda event: self._handle_save_shortcut())
        self.bind("<Command-s>", lambda event: self._handle_save_shortcut())  # macOS

        # Ctrl/Cmd+C: Already handled by system for copy, but we can add custom behavior
        # F5: Refresh/Fetch Games
        self.bind("<F5>", lambda event: self._handle_refresh_shortcut())

        logger.info("Keyboard shortcuts initialized")

    def _handle_save_shortcut(self):
        """Handle Ctrl+S keyboard shortcut."""
        # Save prompt if we're in the Preview tab
        if "Preview" in self.tabs:
            preview_tab = self.tabs["Preview"]
            if hasattr(preview_tab, 'save_prompt'):
                preview_tab.save_prompt()
                self._update_status("Prompt saved!", "success")
            else:
                logger.warning("Preview tab doesn't have save_prompt method")

    def _handle_refresh_shortcut(self):
        """Handle F5 keyboard shortcut to refresh/fetch games."""
        # Fetch games if we're in the Games tab
        if "Games" in self.tabs:
            games_tab = self.tabs["Games"]
            if hasattr(games_tab, '_fetch_games'):
                games_tab._fetch_games()
                logger.info("Fetching games via F5 shortcut")

    def _update_status(self, message: str, status_type: str = "success"):
        """Update the status indicator."""
        colors = get_theme_colors(self.theme)
        color_map = {
            "success": colors["success"],
            "warning": colors["warning"],
            "error": colors["error"]
        }
        self.status_label.configure(
            text=f"● {message}",
            text_color=color_map.get(status_type, colors["success"])
        )
        # Reset status after specified timeout
        self.after(self.STATUS_RESET_TIMEOUT_MS, lambda: self.status_label.configure(
            text="● Ready",
            text_color=colors["success"]
        ))


if __name__ == "__main__":
    app = PromptBuilderApp()
    app.mainloop()
