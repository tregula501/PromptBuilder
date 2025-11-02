"""
Sports Selection Tab - UI for selecting sports and leagues.
"""

import customtkinter as ctk
from typing import Dict, List, Set
import logging

from app.core.models import SportType
from app.core.config import get_config
from app.ui.styles import (
    COLORS, FONTS, SPACING, DIMENSIONS,
    get_theme_colors, get_frame_style
)

logger = logging.getLogger(__name__)


class SportsSelectionTab(ctk.CTkScrollableFrame):
    """Tab for selecting which sports to include in the prompt."""

    def __init__(self, parent, on_selection_change=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.config = get_config()
        self.theme = self.config.get_setting("theme", "dark")
        self.colors = get_theme_colors(self.theme)

        # Callback for selection changes (for undo/redo)
        self.on_selection_change = on_selection_change

        # Store checkbox variables
        self.sport_vars: Dict[SportType, ctk.BooleanVar] = {}

        # Selected sports set
        self.selected_sports: Set[SportType] = set()

        # Create UI
        self._create_ui()

        # Load saved preferences
        self._load_preferences()

    def _create_ui(self):
        """Create the sports selection UI."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)

        # Header
        header_label = ctk.CTkLabel(
            self,
            text="Select Sports to Analyze",
            font=FONTS["heading_small"],
            text_color=self.colors["text_primary"]
        )
        header_label.grid(row=0, column=0, padx=SPACING["xl"], pady=(SPACING["xl"], SPACING["md"]), sticky="w")

        # Description
        desc_label = ctk.CTkLabel(
            self,
            text="Choose which sports you want to include in your betting prompt analysis.",
            font=FONTS["body_medium"],
            text_color=self.colors["text_secondary"]
        )
        desc_label.grid(row=1, column=0, padx=SPACING["xl"], pady=(0, SPACING["lg"]), sticky="w")

        # Sport categories
        self._create_sport_category("American Sports", [
            SportType.NFL,
            SportType.NBA,
            SportType.MLB,
            SportType.NHL,
            SportType.NCAAF,
            SportType.NCAAB
        ], start_row=2)

        self._create_sport_category("Soccer / Football", [
            SportType.SOCCER,
            SportType.PREMIER_LEAGUE,
            SportType.LA_LIGA,
            SportType.CHAMPIONS_LEAGUE
        ], start_row=10)

        self._create_sport_category("Combat Sports & Other", [
            SportType.MMA,
            SportType.UFC,
            SportType.BOXING,
            SportType.TENNIS,
            SportType.GOLF
        ], start_row=17)

        # Action buttons
        self._create_action_buttons(start_row=25)

    def _create_sport_category(self, category_name: str, sports: List[SportType], start_row: int):
        """Create a category section with sports checkboxes."""
        # Category frame
        category_frame = ctk.CTkFrame(
            self,
            **get_frame_style("card", self.theme)
        )
        category_frame.grid(
            row=start_row,
            column=0,
            padx=SPACING["xl"],
            pady=SPACING["md"],
            sticky="ew"
        )
        category_frame.grid_columnconfigure(0, weight=1)

        # Category header
        cat_header = ctk.CTkLabel(
            category_frame,
            text=category_name,
            font=FONTS["heading_small"],
            text_color=self.colors["accent"]
        )
        cat_header.grid(row=0, column=0, padx=SPACING["lg"], pady=(SPACING["lg"], SPACING["sm"]), sticky="w")

        # Sports checkboxes
        for idx, sport in enumerate(sports, start=1):
            self._create_sport_checkbox(category_frame, sport, idx)

    def _create_sport_checkbox(self, parent, sport: SportType, row: int):
        """Create a checkbox for a sport."""
        # Create boolean variable
        var = ctk.BooleanVar(value=False)
        self.sport_vars[sport] = var

        # Create checkbox
        checkbox = ctk.CTkCheckBox(
            parent,
            text=sport.value,
            variable=var,
            font=FONTS["body_medium"],
            text_color=self.colors["text_primary"],
            fg_color=self.colors["accent"],
            hover_color=self.colors["accent_hover"],
            command=lambda s=sport: self._on_sport_toggle(s)
        )
        checkbox.grid(row=row, column=0, padx=SPACING["xl"], pady=SPACING["xs"], sticky="w")

    def _create_action_buttons(self, start_row: int):
        """Create action buttons (Select All, Clear, etc.)."""
        button_frame = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        button_frame.grid(row=start_row, column=0, padx=SPACING["xl"], pady=SPACING["xl"], sticky="ew")
        button_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Select All button
        select_all_btn = ctk.CTkButton(
            button_frame,
            text="Select All",
            font=FONTS["body_medium"],
            fg_color=self.colors["bg_tertiary"],
            hover_color=self.colors["accent"],
            height=DIMENSIONS["button_height"],
            command=self._select_all
        )
        select_all_btn.grid(row=0, column=0, padx=SPACING["sm"], sticky="ew")

        # Clear All button
        clear_btn = ctk.CTkButton(
            button_frame,
            text="Clear All",
            font=FONTS["body_medium"],
            fg_color=self.colors["bg_tertiary"],
            hover_color=self.colors["error"],
            height=DIMENSIONS["button_height"],
            command=self._clear_all
        )
        clear_btn.grid(row=0, column=1, padx=SPACING["sm"], sticky="ew")

        # Save Preferences button
        save_btn = ctk.CTkButton(
            button_frame,
            text="Save as Default",
            font=FONTS["body_medium"],
            fg_color=self.colors["success"],
            hover_color="#3ece70",
            height=DIMENSIONS["button_height"],
            command=self._save_preferences
        )
        save_btn.grid(row=0, column=2, padx=SPACING["sm"], sticky="ew")

        # Selection count label
        self.count_label = ctk.CTkLabel(
            button_frame,
            text="0 sports selected",
            font=FONTS["body_small"],
            text_color=self.colors["text_secondary"]
        )
        self.count_label.grid(row=1, column=0, columnspan=3, pady=(SPACING["sm"], 0))

    def _on_sport_toggle(self, sport: SportType):
        """Handle sport checkbox toggle."""
        # Capture old state for undo/redo
        old_state = list(self.selected_sports)

        if self.sport_vars[sport].get():
            self.selected_sports.add(sport)
            logger.info(f"Selected sport: {sport.value}")
        else:
            self.selected_sports.discard(sport)
            logger.info(f"Deselected sport: {sport.value}")

        self._update_count()

        # Record change for undo/redo
        if self.on_selection_change:
            new_state = list(self.selected_sports)
            self.on_selection_change(old_state, new_state)

    def _update_count(self):
        """Update the selection count label."""
        count = len(self.selected_sports)
        plural = "s" if count != 1 else ""
        self.count_label.configure(text=f"{count} sport{plural} selected")

    def _select_all(self):
        """Select all sports."""
        # Capture old state for undo/redo
        old_state = list(self.selected_sports)

        for sport, var in self.sport_vars.items():
            var.set(True)
            self.selected_sports.add(sport)
        self._update_count()
        logger.info("Selected all sports")

        # Record change for undo/redo
        if self.on_selection_change:
            new_state = list(self.selected_sports)
            self.on_selection_change(old_state, new_state)

    def _clear_all(self):
        """Clear all sports."""
        # Capture old state for undo/redo
        old_state = list(self.selected_sports)

        for sport, var in self.sport_vars.items():
            var.set(False)
        self.selected_sports.clear()
        self._update_count()
        logger.info("Cleared all sports")

        # Record change for undo/redo
        if self.on_selection_change:
            new_state = list(self.selected_sports)
            self.on_selection_change(old_state, new_state)

    def _save_preferences(self):
        """Save current selection as default preferences."""
        selected_list = [sport.value for sport in self.selected_sports]
        self.config.set_setting("selected_sports", selected_list)
        logger.info(f"Saved {len(selected_list)} sports as default preferences")

        # Show confirmation
        self.count_label.configure(text=f"✓ Saved {len(selected_list)} sports as default!")
        self.after(2000, self._update_count)  # Reset after 2 seconds

    def _load_preferences(self):
        """Load saved sport preferences."""
        saved_sports = self.config.get_setting("selected_sports", ["NFL", "NBA"])

        for sport_name in saved_sports:
            try:
                sport = SportType(sport_name)
                if sport in self.sport_vars:
                    self.sport_vars[sport].set(True)
                    self.selected_sports.add(sport)
            except ValueError:
                logger.warning(f"Unknown sport in saved preferences: {sport_name}")

        self._update_count()
        logger.info(f"Loaded {len(self.selected_sports)} sports from preferences")

    def get_selected_sports(self) -> List[SportType]:
        """Get the list of selected sports."""
        return list(self.selected_sports)

    def set_selected_sports(self, sports: List[SportType]):
        """Set the selected sports programmatically."""
        # Clear current selection
        self._clear_all()

        # Set new selection
        for sport in sports:
            if sport in self.sport_vars:
                self.sport_vars[sport].set(True)
                self.selected_sports.add(sport)

        self._update_count()
