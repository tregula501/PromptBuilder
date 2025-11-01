"""
Bet Configuration Tab - UI for configuring bet types, odds, and risk.
"""

import customtkinter as ctk
from typing import Dict, List, Set
import logging

from app.core.models import BetType, RiskLevel, AnalysisType
from app.core.config import get_config
from app.ui.styles import (
    COLORS, FONTS, SPACING, DIMENSIONS,
    get_theme_colors, get_frame_style, get_button_style
)

logger = logging.getLogger(__name__)


class BetConfigurationTab(ctk.CTkScrollableFrame):
    """Tab for configuring bet parameters."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        self.config = get_config()
        self.theme = self.config.get_setting("theme", "dark")
        self.colors = get_theme_colors(self.theme)

        # State variables
        self.bet_type_vars: Dict[BetType, ctk.BooleanVar] = {}
        self.selected_bet_types: Set[BetType] = set()

        self.analysis_vars: Dict[AnalysisType, ctk.BooleanVar] = {}
        self.selected_analyses: Set[AnalysisType] = set()

        self.sportsbook_vars: Dict[str, ctk.BooleanVar] = {}
        self.selected_sportsbooks: Set[str] = set()

        self.max_odds_var = ctk.IntVar(value=400)
        self.risk_level_var = ctk.StringVar(value="Medium")

        # Include options
        self.include_stats_var = ctk.BooleanVar(value=True)
        self.include_injuries_var = ctk.BooleanVar(value=True)
        self.include_weather_var = ctk.BooleanVar(value=True)
        self.include_trends_var = ctk.BooleanVar(value=True)

        # Create UI
        self._create_ui()

    def _create_ui(self):
        """Create the bet configuration UI."""
        self.grid_columnconfigure(0, weight=1)

        row = 0

        # Header
        header = ctk.CTkLabel(
            self,
            text="Bet Configuration",
            font=FONTS["heading_small"],
            text_color=self.colors["text_primary"]
        )
        header.grid(row=row, column=0, padx=SPACING["xl"], pady=(SPACING["xl"], SPACING["md"]), sticky="w")
        row += 1

        # Odds Limit Section
        row = self._create_odds_limit_section(row)

        # Bet Types Section
        row = self._create_bet_types_section(row)

        # Risk Tolerance Section
        row = self._create_risk_section(row)

        # Analysis Types Section
        row = self._create_analysis_section(row)

        # Include Options Section
        row = self._create_include_options_section(row)

        # Sportsbook Filter Section
        row = self._create_sportsbook_section(row)

        # Save button
        self._create_save_button(row)

    def _create_odds_limit_section(self, start_row: int) -> int:
        """Create the odds limit configuration section."""
        # Frame
        frame = ctk.CTkFrame(self, **get_frame_style("card", self.theme))
        frame.grid(row=start_row, column=0, padx=SPACING["xl"], pady=SPACING["md"], sticky="ew")
        frame.grid_columnconfigure(0, weight=1)

        # Title
        title = ctk.CTkLabel(
            frame,
            text="Maximum Combined Odds",
            font=FONTS["heading_small"],
            text_color=self.colors["accent"]
        )
        title.grid(row=0, column=0, padx=SPACING["lg"], pady=(SPACING["lg"], SPACING["sm"]), sticky="w")

        # Description
        desc = ctk.CTkLabel(
            frame,
            text="Set the maximum total odds for parlay bets (American format, e.g., +400)",
            font=FONTS["body_small"],
            text_color=self.colors["text_secondary"]
        )
        desc.grid(row=1, column=0, padx=SPACING["lg"], pady=(0, SPACING["md"]), sticky="w")

        # Slider
        slider = ctk.CTkSlider(
            frame,
            from_=100,
            to=2000,
            number_of_steps=38,  # 50-unit increments
            variable=self.max_odds_var,
            command=self._on_odds_change,
            fg_color=self.colors["bg_tertiary"],
            progress_color=self.colors["accent"],
            button_color=self.colors["accent"],
            button_hover_color=self.colors["accent_hover"]
        )
        slider.grid(row=2, column=0, padx=SPACING["lg"], pady=SPACING["md"], sticky="ew")

        # Value label
        self.odds_value_label = ctk.CTkLabel(
            frame,
            text=f"+{self.max_odds_var.get()}",
            font=FONTS["heading_medium"],
            text_color=self.colors["success"]
        )
        self.odds_value_label.grid(row=3, column=0, padx=SPACING["lg"], pady=(0, SPACING["lg"]))

        return start_row + 1

    def _create_bet_types_section(self, start_row: int) -> int:
        """Create bet types selection section."""
        frame = ctk.CTkFrame(self, **get_frame_style("card", self.theme))
        frame.grid(row=start_row, column=0, padx=SPACING["xl"], pady=SPACING["md"], sticky="ew")
        frame.grid_columnconfigure((0, 1), weight=1)

        # Title
        title = ctk.CTkLabel(
            frame,
            text="Bet Types to Include",
            font=FONTS["heading_small"],
            text_color=self.colors["accent"]
        )
        title.grid(row=0, column=0, columnspan=2, padx=SPACING["lg"], pady=(SPACING["lg"], SPACING["sm"]), sticky="w")

        # Bet type checkboxes
        bet_types = [
            (BetType.MONEYLINE, "Moneyline", "Straight win/loss bets"),
            (BetType.SPREAD, "Spread", "Point spread bets"),
            (BetType.TOTALS, "Totals (Over/Under)", "Combined score over/under"),
            (BetType.PARLAY, "Parlay", "Multiple selections combined"),
            (BetType.PROP, "Player Props", "Player performance bets"),
            (BetType.TEASER, "Teasers", "Adjusted point spreads"),
        ]

        for idx, (bet_type, label, description) in enumerate(bet_types, start=1):
            var = ctk.BooleanVar(value=bet_type in [BetType.MONEYLINE, BetType.SPREAD, BetType.TOTALS])
            self.bet_type_vars[bet_type] = var

            col = idx % 2
            row = 1 + (idx // 2)

            checkbox = ctk.CTkCheckBox(
                frame,
                text=label,
                variable=var,
                font=FONTS["body_medium"],
                text_color=self.colors["text_primary"],
                fg_color=self.colors["accent"],
                command=lambda bt=bet_type: self._on_bet_type_toggle(bt)
            )
            checkbox.grid(row=row, column=col, padx=SPACING["lg"], pady=SPACING["xs"], sticky="w")

            # Set initial state
            if var.get():
                self.selected_bet_types.add(bet_type)

        return start_row + 1

    def _create_risk_section(self, start_row: int) -> int:
        """Create risk tolerance section."""
        frame = ctk.CTkFrame(self, **get_frame_style("card", self.theme))
        frame.grid(row=start_row, column=0, padx=SPACING["xl"], pady=SPACING["md"], sticky="ew")
        frame.grid_columnconfigure(0, weight=1)

        # Title
        title = ctk.CTkLabel(
            frame,
            text="Risk Tolerance",
            font=FONTS["heading_small"],
            text_color=self.colors["accent"]
        )
        title.grid(row=0, column=0, padx=SPACING["lg"], pady=(SPACING["lg"], SPACING["sm"]), sticky="w")

        # Radio buttons
        risk_frame = ctk.CTkFrame(frame, fg_color="transparent")
        risk_frame.grid(row=1, column=0, padx=SPACING["lg"], pady=SPACING["md"], sticky="ew")
        risk_frame.grid_columnconfigure((0, 1, 2), weight=1)

        for idx, (level, desc, color) in enumerate([
            (RiskLevel.LOW, "Conservative approach, safer bets", "success"),
            (RiskLevel.MEDIUM, "Balanced risk/reward", "warning"),
            (RiskLevel.HIGH, "Aggressive approach, higher variance", "error")
        ]):
            radio = ctk.CTkRadioButton(
                risk_frame,
                text=f"{level.value}\n{desc}",
                variable=self.risk_level_var,
                value=level.value,
                font=FONTS["body_medium"],
                text_color=self.colors["text_primary"],
                fg_color=self.colors[color],
                hover_color=self.colors[color]
            )
            radio.grid(row=0, column=idx, padx=SPACING["sm"], pady=SPACING["md"], sticky="ew")

        return start_row + 1

    def _create_analysis_section(self, start_row: int) -> int:
        """Create analysis types section."""
        frame = ctk.CTkFrame(self, **get_frame_style("card", self.theme))
        frame.grid(row=start_row, column=0, padx=SPACING["xl"], pady=SPACING["md"], sticky="ew")
        frame.grid_columnconfigure(0, weight=1)

        # Title
        title = ctk.CTkLabel(
            frame,
            text="Analysis Focus Areas",
            font=FONTS["heading_small"],
            text_color=self.colors["accent"]
        )
        title.grid(row=0, column=0, padx=SPACING["lg"], pady=(SPACING["lg"], SPACING["sm"]), sticky="w")

        # Analysis checkboxes
        analyses = [
            (AnalysisType.VALUE_BETTING, "Value Betting", "Find +EV opportunities"),
            (AnalysisType.RISK_ASSESSMENT, "Risk Assessment", "Detailed risk analysis"),
            (AnalysisType.STATISTICAL_PREDICTIONS, "Statistical Predictions", "Data-driven predictions"),
            (AnalysisType.TREND_ANALYSIS, "Trend Analysis", "Recent patterns and momentum"),
        ]

        for idx, (analysis_type, label, desc) in enumerate(analyses, start=1):
            var = ctk.BooleanVar(value=True)
            self.analysis_vars[analysis_type] = var
            self.selected_analyses.add(analysis_type)

            checkbox = ctk.CTkCheckBox(
                frame,
                text=f"{label} - {desc}",
                variable=var,
                font=FONTS["body_medium"],
                text_color=self.colors["text_primary"],
                fg_color=self.colors["accent"],
                command=lambda at=analysis_type: self._on_analysis_toggle(at)
            )
            checkbox.grid(row=idx, column=0, padx=SPACING["lg"], pady=SPACING["xs"], sticky="w")

        return start_row + 1

    def _create_include_options_section(self, start_row: int) -> int:
        """Create include options section."""
        frame = ctk.CTkFrame(self, **get_frame_style("card", self.theme))
        frame.grid(row=start_row, column=0, padx=SPACING["xl"], pady=SPACING["md"], sticky="ew")
        frame.grid_columnconfigure((0, 1), weight=1)

        # Title
        title = ctk.CTkLabel(
            frame,
            text="Include in Analysis",
            font=FONTS["heading_small"],
            text_color=self.colors["accent"]
        )
        title.grid(row=0, column=0, columnspan=2, padx=SPACING["lg"], pady=(SPACING["lg"], SPACING["sm"]), sticky="w")

        # Options
        options = [
            (self.include_stats_var, "Team/Player Statistics"),
            (self.include_injuries_var, "Injury Reports"),
            (self.include_weather_var, "Weather Conditions"),
            (self.include_trends_var, "Recent Trends & Form")
        ]

        for idx, (var, label) in enumerate(options):
            col = idx % 2
            row = 1 + (idx // 2)

            checkbox = ctk.CTkCheckBox(
                frame,
                text=label,
                variable=var,
                font=FONTS["body_medium"],
                text_color=self.colors["text_primary"],
                fg_color=self.colors["accent"]
            )
            checkbox.grid(row=row, column=col, padx=SPACING["lg"], pady=SPACING["xs"], sticky="w")

        return start_row + 1

    def _create_sportsbook_section(self, start_row: int) -> int:
        """Create sportsbook filter section."""
        frame = ctk.CTkFrame(self, **get_frame_style("card", self.theme))
        frame.grid(row=start_row, column=0, padx=SPACING["xl"], pady=SPACING["md"], sticky="ew")
        frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Title
        title = ctk.CTkLabel(
            frame,
            text="Sportsbook Filter",
            font=FONTS["heading_small"],
            text_color=self.colors["accent"]
        )
        title.grid(row=0, column=0, columnspan=3, padx=SPACING["lg"], pady=(SPACING["lg"], SPACING["sm"]), sticky="w")

        # Description
        desc = ctk.CTkLabel(
            frame,
            text="Select which sportsbooks to display in odds (leave all unchecked to show all)",
            font=FONTS["body_small"],
            text_color=self.colors["text_secondary"]
        )
        desc.grid(row=1, column=0, columnspan=3, padx=SPACING["lg"], pady=(0, SPACING["md"]), sticky="w")

        # Common sportsbooks
        sportsbooks = [
            "DraftKings",
            "FanDuel",
            "BetMGM",
            "Caesars",
            "PointsBet",
            "BetRivers",
            "Unibet",
            "WynnBET",
            "ESPN BET",
            "Bet365",
            "Bovada",
            "MyBookie"
        ]

        # Select All / Clear All buttons
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.grid(row=2, column=0, columnspan=3, padx=SPACING["lg"], pady=SPACING["sm"], sticky="w")

        select_all_btn = ctk.CTkButton(
            btn_frame,
            text="Select All",
            font=FONTS["body_small"],
            **get_button_style("secondary", self.theme),
            width=100,
            height=28,
            command=self._select_all_sportsbooks
        )
        select_all_btn.grid(row=0, column=0, padx=SPACING["xs"])

        clear_all_btn = ctk.CTkButton(
            btn_frame,
            text="Clear All",
            font=FONTS["body_small"],
            **get_button_style("secondary", self.theme),
            width=100,
            height=28,
            command=self._clear_all_sportsbooks
        )
        clear_all_btn.grid(row=0, column=1, padx=SPACING["xs"])

        # Sportsbook checkboxes (3 columns)
        for idx, sportsbook in enumerate(sportsbooks):
            var = ctk.BooleanVar(value=False)  # Default: show all (none selected)
            self.sportsbook_vars[sportsbook] = var

            col = idx % 3
            row = 3 + (idx // 3)

            checkbox = ctk.CTkCheckBox(
                frame,
                text=sportsbook,
                variable=var,
                font=FONTS["body_medium"],
                text_color=self.colors["text_primary"],
                fg_color=self.colors["accent"],
                command=lambda sb=sportsbook: self._on_sportsbook_toggle(sb)
            )
            checkbox.grid(row=row, column=col, padx=SPACING["lg"], pady=SPACING["xs"], sticky="w")

        return start_row + 1

    def _create_save_button(self, start_row: int):
        """Create save configuration button."""
        btn = ctk.CTkButton(
            self,
            text="Save Configuration as Default",
            font=FONTS["body_medium"],
            **get_button_style("success", self.theme),
            height=DIMENSIONS["button_height"],
            command=self._save_configuration
        )
        btn.grid(row=start_row, column=0, padx=SPACING["xl"], pady=SPACING["xl"], sticky="ew")

    def _on_odds_change(self, value):
        """Handle odds slider change."""
        odds_val = int(value)
        self.odds_value_label.configure(text=f"+{odds_val}")

    def _on_bet_type_toggle(self, bet_type: BetType):
        """Handle bet type checkbox toggle."""
        if self.bet_type_vars[bet_type].get():
            self.selected_bet_types.add(bet_type)
        else:
            self.selected_bet_types.discard(bet_type)

    def _on_analysis_toggle(self, analysis_type: AnalysisType):
        """Handle analysis type checkbox toggle."""
        if self.analysis_vars[analysis_type].get():
            self.selected_analyses.add(analysis_type)
        else:
            self.selected_analyses.discard(analysis_type)

    def _on_sportsbook_toggle(self, sportsbook: str):
        """Handle sportsbook checkbox toggle."""
        if self.sportsbook_vars[sportsbook].get():
            self.selected_sportsbooks.add(sportsbook)
        else:
            self.selected_sportsbooks.discard(sportsbook)

    def _select_all_sportsbooks(self):
        """Select all sportsbooks."""
        for sportsbook, var in self.sportsbook_vars.items():
            var.set(True)
            self.selected_sportsbooks.add(sportsbook)

    def _clear_all_sportsbooks(self):
        """Clear all sportsbook selections."""
        for sportsbook, var in self.sportsbook_vars.items():
            var.set(False)
            self.selected_sportsbooks.discard(sportsbook)

    def _save_configuration(self):
        """Save current configuration as default."""
        self.config.update_settings({
            "max_combined_odds": self.max_odds_var.get(),
            "bet_types": {bt.value: (bt in self.selected_bet_types) for bt in BetType},
            "risk_tolerance": self.risk_level_var.get(),
            "analysis_types": {at.value: (at in self.selected_analyses) for at in AnalysisType},
            "include_stats": self.include_stats_var.get(),
            "include_injuries": self.include_injuries_var.get(),
            "include_weather": self.include_weather_var.get(),
            "include_trends": self.include_trends_var.get(),
            "selected_sportsbooks": list(self.selected_sportsbooks)
        })
        logger.info("Saved bet configuration as default")

    def get_configuration(self) -> dict:
        """Get current bet configuration."""
        return {
            "max_odds": self.max_odds_var.get(),
            "bet_types": list(self.selected_bet_types),
            "risk_level": RiskLevel(self.risk_level_var.get()),
            "analysis_types": list(self.selected_analyses),
            "include_stats": self.include_stats_var.get(),
            "include_injuries": self.include_injuries_var.get(),
            "include_weather": self.include_weather_var.get(),
            "include_trends": self.include_trends_var.get(),
            "selected_sportsbooks": list(self.selected_sportsbooks)
        }
