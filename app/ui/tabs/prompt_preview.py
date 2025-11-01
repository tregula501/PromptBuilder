"""
Prompt Preview Tab - UI for previewing and managing generated prompts.
"""

import customtkinter as ctk
from pathlib import Path
import logging

from app.core.config import get_config
from app.ui.styles import (
    COLORS, FONTS, SPACING, DIMENSIONS,
    get_theme_colors, get_button_style, get_frame_style
)

logger = logging.getLogger(__name__)


class PromptPreviewTab(ctk.CTkFrame):
    """Tab for previewing and managing generated prompts."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        self.config = get_config()
        self.theme = self.config.get_setting("theme", "dark")
        self.colors = get_theme_colors(self.theme)

        self.current_prompt = ""

        # Create UI
        self._create_ui()

    def _create_ui(self):
        """Create the prompt preview UI."""
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Header with actions
        self._create_header()

        # Prompt text area
        self._create_text_area()

        # Footer with stats
        self._create_footer()

    def _create_header(self):
        """Create header with title and action buttons."""
        header_frame = ctk.CTkFrame(self, **get_frame_style("card", self.theme))
        header_frame.grid(row=0, column=0, padx=SPACING["xl"], pady=(SPACING["xl"], SPACING["md"]), sticky="ew")
        header_frame.grid_columnconfigure(1, weight=1)

        # Title
        title = ctk.CTkLabel(
            header_frame,
            text="📝 Generated Prompt",
            font=FONTS["heading_medium"],
            text_color=self.colors["text_primary"]
        )
        title.grid(row=0, column=0, padx=SPACING["lg"], pady=SPACING["lg"], sticky="w")

        # Button frame
        btn_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        btn_frame.grid(row=0, column=2, padx=SPACING["lg"], pady=SPACING["lg"], sticky="e")

        # Copy button
        self.copy_btn = ctk.CTkButton(
            btn_frame,
            text="📋 Copy",
            font=FONTS["body_medium"],
            **get_button_style("primary", self.theme),
            width=100,
            height=DIMENSIONS["button_height"],
            command=self._copy_to_clipboard
        )
        self.copy_btn.grid(row=0, column=0, padx=SPACING["sm"])

        # Save button
        self.save_btn = ctk.CTkButton(
            btn_frame,
            text="💾 Save",
            font=FONTS["body_medium"],
            **get_button_style("success", self.theme),
            width=100,
            height=DIMENSIONS["button_height"],
            command=self._save_prompt
        )
        self.save_btn.grid(row=0, column=1, padx=SPACING["sm"])

        # Export button
        self.export_btn = ctk.CTkButton(
            btn_frame,
            text="📤 Export",
            font=FONTS["body_medium"],
            **get_button_style("secondary", self.theme),
            width=100,
            height=DIMENSIONS["button_height"],
            command=self._export_prompt
        )
        self.export_btn.grid(row=0, column=2, padx=SPACING["sm"])

    def _create_text_area(self):
        """Create the main text area for prompt display."""
        # Frame for text area
        text_frame = ctk.CTkFrame(self, **get_frame_style("card", self.theme))
        text_frame.grid(row=1, column=0, padx=SPACING["xl"], pady=SPACING["md"], sticky="nsew")
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)

        # Text widget
        self.text_area = ctk.CTkTextbox(
            text_frame,
            font=FONTS["mono"],
            fg_color=self.colors["bg_primary"],
            text_color=self.colors["text_primary"],
            border_width=0,
            wrap="word"
        )
        self.text_area.grid(row=0, column=0, padx=SPACING["md"], pady=SPACING["md"], sticky="nsew")

        # Placeholder text
        self.set_prompt("Click 'Generate Prompt' to create your betting analysis prompt.\n\n"
                       "The prompt will appear here with:\n"
                       "- Selected sports and games\n"
                       "- Betting odds from configured sources\n"
                       "- Analysis parameters\n"
                       "- Instructions for AI analysis\n\n"
                       "You can then copy it and use with Claude, GPT-4, or other AI models.")

    def _create_footer(self):
        """Create footer with prompt statistics."""
        footer_frame = ctk.CTkFrame(self, **get_frame_style("card", self.theme))
        footer_frame.grid(row=2, column=0, padx=SPACING["xl"], pady=(SPACING["md"], SPACING["xl"]), sticky="ew")
        footer_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Character count
        self.char_label = ctk.CTkLabel(
            footer_frame,
            text="Characters: 0",
            font=FONTS["body_small"],
            text_color=self.colors["text_secondary"]
        )
        self.char_label.grid(row=0, column=0, padx=SPACING["lg"], pady=SPACING["md"], sticky="w")

        # Word count
        self.word_label = ctk.CTkLabel(
            footer_frame,
            text="Words: 0",
            font=FONTS["body_small"],
            text_color=self.colors["text_secondary"]
        )
        self.word_label.grid(row=0, column=1, padx=SPACING["lg"], pady=SPACING["md"])

        # Status
        self.status_label = ctk.CTkLabel(
            footer_frame,
            text="Ready",
            font=FONTS["body_small"],
            text_color=self.colors["success"]
        )
        self.status_label.grid(row=0, column=2, padx=SPACING["lg"], pady=SPACING["md"], sticky="e")

    def set_prompt(self, prompt_text: str):
        """Set the prompt text and update stats."""
        self.current_prompt = prompt_text

        # Update text area
        self.text_area.delete("1.0", "end")
        self.text_area.insert("1.0", prompt_text)

        # Update stats
        char_count = len(prompt_text)
        word_count = len(prompt_text.split())

        self.char_label.configure(text=f"Characters: {char_count:,}")
        self.word_label.configure(text=f"Words: {word_count:,}")

        logger.info(f"Prompt set: {char_count} chars, {word_count} words")

    def get_prompt(self) -> str:
        """Get the current prompt text."""
        return self.text_area.get("1.0", "end").strip()

    def _copy_to_clipboard(self):
        """Copy prompt to clipboard."""
        prompt = self.get_prompt()
        if not prompt:
            self._update_status("No prompt to copy", "error")
            return

        try:
            self.clipboard_clear()
            self.clipboard_append(prompt)
            self._update_status("Copied to clipboard!", "success")
            logger.info("Prompt copied to clipboard")
        except Exception as e:
            self._update_status(f"Copy failed: {str(e)}", "error")
            logger.error(f"Failed to copy to clipboard: {e}")

    def _save_prompt(self):
        """Save prompt to file."""
        prompt = self.get_prompt()
        if not prompt:
            self._update_status("No prompt to save", "error")
            return

        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"prompt_{timestamp}.txt"
            filepath = self.config.PROMPTS_DIR / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(prompt)

            self._update_status(f"Saved: {filename}", "success")
            logger.info(f"Prompt saved to: {filepath}")
        except Exception as e:
            self._update_status(f"Save failed: {str(e)}", "error")
            logger.error(f"Failed to save prompt: {e}")

    def _export_prompt(self):
        """Export prompt with file dialog."""
        from tkinter import filedialog

        prompt = self.get_prompt()
        if not prompt:
            self._update_status("No prompt to export", "error")
            return

        try:
            filepath = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("Markdown files", "*.md"), ("All files", "*.*")],
                initialfile=f"betting_prompt_{self._get_timestamp()}.txt"
            )

            if filepath:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(prompt)

                self._update_status(f"Exported to: {Path(filepath).name}", "success")
                logger.info(f"Prompt exported to: {filepath}")
        except Exception as e:
            self._update_status(f"Export failed: {str(e)}", "error")
            logger.error(f"Failed to export prompt: {e}")

    def _update_status(self, message: str, status_type: str = "success"):
        """Update status label."""
        color_map = {
            "success": self.colors["success"],
            "error": self.colors["error"],
            "warning": self.colors["warning"]
        }

        self.status_label.configure(
            text=message,
            text_color=color_map.get(status_type, self.colors["text_secondary"])
        )

        # Reset after 3 seconds
        if status_type != "error":
            self.after(3000, lambda: self.status_label.configure(
                text="Ready",
                text_color=self.colors["success"]
            ))

    def _get_timestamp(self):
        """Get formatted timestamp."""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def clear(self):
        """Clear the prompt display."""
        self.text_area.delete("1.0", "end")
        self.current_prompt = ""
        self.char_label.configure(text="Characters: 0")
        self.word_label.configure(text="Words: 0")
