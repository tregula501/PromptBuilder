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
from app.core.command_history import get_command_history, SelectionCommand

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

        # Validation state
        self.validation_state = {
            "sports_selected": False,
            "games_selected": False
        }

        # Command history for undo/redo
        self.command_history = get_command_history()

        # Create UI elements
        self._create_sidebar()
        self._create_main_content()

        # Bind keyboard shortcuts
        self._setup_keyboard_shortcuts()

        # Start validation check loop
        self._start_validation_check()

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
        self.nav_button_icons = {
            "Sports": "🏈",
            "Games": "📋",
            "Odds": "💰",
            "Bet Config": "⚙️",
            "Preview": "👁️",
        }
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

        # Undo/Redo button frame
        undo_redo_frame = ctk.CTkFrame(
            self.sidebar,
            fg_color="transparent"
        )
        undo_redo_frame.grid(row=9, column=0, padx=SPACING["lg"], pady=(SPACING["md"], SPACING["xs"]), sticky="ew")
        undo_redo_frame.grid_columnconfigure((0, 1), weight=1)

        self.undo_btn = ctk.CTkButton(
            undo_redo_frame,
            text="↶ Undo",
            font=FONTS["body_small"],
            fg_color=colors["bg_tertiary"],
            hover_color=colors["accent"],
            height=32,
            command=self._undo,
            state="disabled"
        )
        self.undo_btn.grid(row=0, column=0, padx=(0, SPACING["xs"]), sticky="ew")

        self.redo_btn = ctk.CTkButton(
            undo_redo_frame,
            text="↷ Redo",
            font=FONTS["body_small"],
            fg_color=colors["bg_tertiary"],
            hover_color=colors["accent"],
            height=32,
            command=self._redo,
            state="disabled"
        )
        self.redo_btn.grid(row=0, column=1, padx=(SPACING["xs"], 0), sticky="ew")

        # Validation feedback label
        self.validation_label = ctk.CTkLabel(
            self.sidebar,
            text="",
            font=FONTS["body_small"],
            text_color=colors["text_secondary"],
            wraplength=DIMENSIONS["sidebar_width"] - (SPACING["lg"] * 2)
        )
        self.validation_label.grid(row=10, column=0, padx=SPACING["lg"], pady=(0, SPACING["xs"]))

        # Generate button
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
            fg_color=colors["bg_primary"],
            on_selection_change=lambda old, new: self.record_selection_change("sports", old, new)
        )

        # Game Selection Tab (NEW)
        self.tabs["Games"] = GameSelectionTab(
            self.content_area,
            fg_color=colors["bg_primary"],
            on_selection_change=lambda old, new: self.record_selection_change("games", old, new)
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
            # Get icon and check mark
            icon = self.nav_button_icons.get(name, "")
            check = ""
            if name == "Sports" and self.validation_state["sports_selected"]:
                check = " ✓"
            elif name == "Games" and self.validation_state["games_selected"]:
                check = " ✓"

            # Update button appearance
            btn_text = f"{icon}  {name}{check}"
            if name == tab_name:
                btn.configure(fg_color=colors["accent"], text=btn_text)
            else:
                btn.configure(fg_color=colors["bg_tertiary"], text=btn_text)

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

        # Ctrl/Cmd+Z: Undo
        self.bind("<Control-z>", lambda event: self._undo())
        self.bind("<Command-z>", lambda event: self._undo())  # macOS

        # Ctrl/Cmd+Y: Redo (Windows/Linux)
        self.bind("<Control-y>", lambda event: self._redo())
        # Ctrl/Cmd+Shift+Z: Redo (macOS standard)
        self.bind("<Control-Shift-Z>", lambda event: self._redo())
        self.bind("<Command-Shift-Z>", lambda event: self._redo())  # macOS

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

    def _check_validation_state(self):
        """Check if all requirements for prompt generation are met."""
        colors = get_theme_colors(self.theme)

        # Check if sports are selected
        sports_tab = self.tabs.get("Sports")
        sports_selected = sports_tab.get_selected_sports() if sports_tab else []
        self.validation_state["sports_selected"] = len(sports_selected) > 0

        # Check if games are selected
        games_tab = self.tabs.get("Games")
        games_selected = games_tab.get_selected_games() if games_tab else []
        self.validation_state["games_selected"] = len(games_selected) > 0

        # Update navigation button indicators
        self._update_nav_indicators()

        # Determine if all requirements are met
        all_valid = all(self.validation_state.values())

        # Update button state
        if all_valid:
            self.generate_btn.configure(
                state="normal",
                fg_color=colors["accent"],
                hover_color=colors["accent_hover"]
            )
            self.validation_label.configure(text="✓ Ready to generate", text_color=colors["success"])
        else:
            self.generate_btn.configure(
                state="disabled",
                fg_color=colors["bg_tertiary"],
                hover_color=colors["bg_tertiary"]
            )

            # Build helpful validation message
            missing_requirements = []
            if not self.validation_state["sports_selected"]:
                missing_requirements.append("⚠ Select at least 1 sport")
            if not self.validation_state["games_selected"]:
                missing_requirements.append("⚠ Select at least 1 game")

            validation_msg = "\n".join(missing_requirements)
            self.validation_label.configure(text=validation_msg, text_color=colors["warning"])

    def _update_nav_indicators(self):
        """Update navigation button text with completion indicators."""
        # Sports tab indicator
        if "Sports" in self.nav_buttons:
            icon = self.nav_button_icons["Sports"]
            check = "✓" if self.validation_state["sports_selected"] else ""
            label = f"{icon}  Sports {check}".strip()
            # Only update if not current tab (to avoid color flickering)
            if self.current_tab != "Sports":
                self.nav_buttons["Sports"].configure(text=label)

        # Games tab indicator
        if "Games" in self.nav_buttons:
            icon = self.nav_button_icons["Games"]
            check = "✓" if self.validation_state["games_selected"] else ""
            label = f"{icon}  Games {check}".strip()
            if self.current_tab != "Games":
                self.nav_buttons["Games"].configure(text=label)

    def _start_validation_check(self):
        """Start periodic validation checking."""
        self._check_validation_state()
        self._update_undo_redo_buttons()
        # Check every 500ms
        self.after(500, self._start_validation_check)

    def _undo(self):
        """Undo the last command."""
        if self.command_history.can_undo():
            self.command_history.undo()
            self._update_undo_redo_buttons()
            self._update_status("Undone", "success")
            logger.info("Undo executed")
        else:
            logger.debug("Cannot undo: no commands in history")

    def _redo(self):
        """Redo the next command."""
        if self.command_history.can_redo():
            self.command_history.redo()
            self._update_undo_redo_buttons()
            self._update_status("Redone", "success")
            logger.info("Redo executed")
        else:
            logger.debug("Cannot redo: at end of history")

    def _update_undo_redo_buttons(self):
        """Update undo/redo button states based on command history."""
        colors = get_theme_colors(self.theme)

        # Update undo button
        if self.command_history.can_undo():
            self.undo_btn.configure(state="normal")
        else:
            self.undo_btn.configure(state="disabled")

        # Update redo button
        if self.command_history.can_redo():
            self.redo_btn.configure(state="normal")
        else:
            self.redo_btn.configure(state="disabled")

    def record_selection_change(self, tab_type: str, old_state, new_state):
        """
        Record a selection change for undo/redo.

        Args:
            tab_type: "sports" or "games"
            old_state: Previous selection state
            new_state: New selection state
        """
        # Get the appropriate tab widget
        if tab_type == "sports":
            tab_widget = self.tabs.get("Sports")
        elif tab_type == "games":
            tab_widget = self.tabs.get("Games")
        else:
            logger.warning(f"Unknown tab type for selection change: {tab_type}")
            return

        if not tab_widget:
            logger.warning(f"Tab widget not found for type: {tab_type}")
            return

        # Don't record if states are identical
        if old_state == new_state:
            return

        # Create and execute command (execute will add it to history)
        command = SelectionCommand(tab_widget, old_state, new_state, tab_type)
        # Don't execute - the change has already been made, just add to history
        # We'll manually add to history
        self.command_history.history.append(command)
        self.command_history.current_index += 1

        # Limit history size
        if len(self.command_history.history) > self.command_history.MAX_HISTORY_SIZE:
            self.command_history.history.pop(0)
            self.command_history.current_index -= 1

        self._update_undo_redo_buttons()
        logger.debug(f"Recorded {tab_type} selection change")


if __name__ == "__main__":
    app = PromptBuilderApp()
    app.mainloop()
