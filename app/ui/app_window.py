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

logger = logging.getLogger(__name__)


class PromptBuilderApp(ctk.CTk):
    """Main application window."""

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
            ("Sports", "📊"),
            ("Bet Config", "⚙️"),
            ("Data Sources", "📡"),
            ("Preview", "👁️"),
            ("Settings", "🔧")
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

        self.save_btn = ctk.CTkButton(
            self.sidebar,
            text="💾 Save & Commit",
            font=FONTS["body_medium"],
            **get_button_style("success", self.theme),
            height=DIMENSIONS["button_height"],
            command=self._save_to_github
        )
        self.save_btn.grid(row=12, column=0, padx=SPACING["lg"], pady=(0, SPACING["lg"]), sticky="ew")

        # Version label
        self.version_label = ctk.CTkLabel(
            self.sidebar,
            text="v1.0.0",
            font=FONTS["body_small"],
            text_color=colors["text_muted"]
        )
        self.version_label.grid(row=13, column=0, padx=SPACING["lg"], pady=(0, SPACING["md"]))

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

        # Tab frames (will be populated later)
        self.tabs = {}
        self._create_placeholder_tabs()

        # Show default tab
        self.current_tab = "Sports"
        self._switch_tab("Sports")

    def _create_placeholder_tabs(self):
        """Create placeholder tabs (will be replaced with actual UI components)."""
        colors = get_theme_colors(self.theme)
        tab_names = ["Sports", "Bet Config", "Data Sources", "Preview", "Settings"]

        for tab_name in tab_names:
            # Create tab frame
            tab_frame = ctk.CTkFrame(
                self.content_area,
                corner_radius=0,
                fg_color=colors["bg_primary"]
            )

            # Placeholder content
            placeholder = ctk.CTkLabel(
                tab_frame,
                text=f"{tab_name} Tab\n\nComing soon...",
                font=FONTS["heading_medium"],
                text_color=colors["text_secondary"]
            )
            placeholder.pack(expand=True)

            self.tabs[tab_name] = tab_frame

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
        # TODO: Implement prompt generation logic
        self._update_status("Prompt generated!", "success")

    def _save_to_github(self):
        """Save prompt to GitHub."""
        self._update_status("Saving to GitHub...", "warning")
        logger.info("Save to GitHub button clicked")
        # TODO: Implement GitHub save logic
        self._update_status("Saved successfully!", "success")

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
        # Reset status after 3 seconds
        self.after(3000, lambda: self.status_label.configure(
            text="● Ready",
            text_color=colors["success"]
        ))


if __name__ == "__main__":
    app = PromptBuilderApp()
    app.mainloop()
