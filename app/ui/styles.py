"""
UI styling and theme configuration for PromptBuilder.
"""

# Color schemes
COLORS = {
    "dark": {
        "bg_primary": "#1a1a1a",
        "bg_secondary": "#2d2d2d",
        "bg_tertiary": "#3d3d3d",
        "accent": "#4a9eff",
        "accent_hover": "#3a8eef",
        "success": "#4ade80",
        "warning": "#fbbf24",
        "error": "#f87171",
        "text_primary": "#ffffff",
        "text_secondary": "#b0b0b0",
        "text_muted": "#707070",
        "border": "#404040"
    },
    "light": {
        "bg_primary": "#ffffff",
        "bg_secondary": "#f5f5f5",
        "bg_tertiary": "#e5e5e5",
        "accent": "#2563eb",
        "accent_hover": "#1d4ed8",
        "success": "#22c55e",
        "warning": "#f59e0b",
        "error": "#ef4444",
        "text_primary": "#1a1a1a",
        "text_secondary": "#4a4a4a",
        "text_muted": "#9a9a9a",
        "border": "#d4d4d4"
    }
}

# Font configurations
FONTS = {
    "heading_large": ("Segoe UI", 24, "bold"),
    "heading_medium": ("Segoe UI", 18, "bold"),
    "heading_small": ("Segoe UI", 14, "bold"),
    "body_large": ("Segoe UI", 13),
    "body_medium": ("Segoe UI", 12),
    "body_small": ("Segoe UI", 11),
    "mono": ("Consolas", 11),
    "mono_small": ("Consolas", 10)
}

# Padding and spacing
SPACING = {
    "xs": 4,
    "sm": 8,
    "md": 12,
    "lg": 16,
    "xl": 24,
    "xxl": 32
}

# Widget dimensions
DIMENSIONS = {
    "button_height": 36,
    "input_height": 32,
    "checkbox_size": 20,
    "tab_height": 40,
    "sidebar_width": 250,
    "min_window_width": 1000,
    "min_window_height": 700
}

# Button styles
BUTTON_STYLES = {
    "primary": {
        "fg_color": COLORS["dark"]["accent"],
        "hover_color": COLORS["dark"]["accent_hover"],
        "text_color": "#ffffff",
        "corner_radius": 6,
        "border_width": 0
    },
    "secondary": {
        "fg_color": COLORS["dark"]["bg_tertiary"],
        "hover_color": COLORS["dark"]["bg_secondary"],
        "text_color": COLORS["dark"]["text_primary"],
        "corner_radius": 6,
        "border_width": 1,
        "border_color": COLORS["dark"]["border"]
    },
    "success": {
        "fg_color": COLORS["dark"]["success"],
        "hover_color": "#3ece70",
        "text_color": "#ffffff",
        "corner_radius": 6,
        "border_width": 0
    },
    "danger": {
        "fg_color": COLORS["dark"]["error"],
        "hover_color": "#e86161",
        "text_color": "#ffffff",
        "corner_radius": 6,
        "border_width": 0
    }
}

# Input field styles
INPUT_STYLES = {
    "default": {
        "corner_radius": 6,
        "border_width": 1,
        "border_color": COLORS["dark"]["border"],
        "fg_color": COLORS["dark"]["bg_secondary"],
        "text_color": COLORS["dark"]["text_primary"]
    }
}

# Frame styles
FRAME_STYLES = {
    "card": {
        "corner_radius": 8,
        "border_width": 1,
        "border_color": COLORS["dark"]["border"],
        "fg_color": COLORS["dark"]["bg_secondary"]
    },
    "transparent": {
        "corner_radius": 0,
        "border_width": 0,
        "fg_color": "transparent"
    }
}


def get_theme_colors(theme="dark"):
    """Get color scheme for specified theme."""
    return COLORS.get(theme, COLORS["dark"])


def get_button_style(style_name="primary", theme="dark"):
    """Get button style configuration."""
    base_style = BUTTON_STYLES.get(style_name, BUTTON_STYLES["primary"]).copy()
    colors = get_theme_colors(theme)

    # Update colors based on theme if needed
    if theme == "light" and style_name in ["primary", "secondary"]:
        if style_name == "primary":
            base_style["fg_color"] = colors["accent"]
            base_style["hover_color"] = colors["accent_hover"]
        else:
            base_style["fg_color"] = colors["bg_tertiary"]
            base_style["hover_color"] = colors["bg_secondary"]
            base_style["text_color"] = colors["text_primary"]
            base_style["border_color"] = colors["border"]

    return base_style


def get_input_style(theme="dark"):
    """Get input field style configuration."""
    colors = get_theme_colors(theme)
    style = INPUT_STYLES["default"].copy()
    style["border_color"] = colors["border"]
    style["fg_color"] = colors["bg_secondary"]
    style["text_color"] = colors["text_primary"]
    return style


def get_frame_style(style_name="card", theme="dark"):
    """Get frame style configuration."""
    colors = get_theme_colors(theme)
    style = FRAME_STYLES.get(style_name, FRAME_STYLES["card"]).copy()

    if style_name == "card":
        style["border_color"] = colors["border"]
        style["fg_color"] = colors["bg_secondary"]

    return style
