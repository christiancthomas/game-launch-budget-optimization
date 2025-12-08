"""
Centralized visualization style system for publication-quality plots.

Uses our brand palette for consistent, professional aesthetics.
"""

import matplotlib.pyplot as plt
import seaborn as sns

# =============================================================================
# BRAND PALETTE
# =============================================================================

# Primary brand color
BLURPLE = "#5555F2"

# Secondary colors
COLORS = {
    "primary": "#5555F2",  # Blurple
    "green": "#2FF579",
    "cyan": "#46F2FB",
    "red": "#F55B53",
    "yellow": "#F5CF22",
    "purple": "#8A57F0",
    # Backgrounds
    "light_bg": "#F5F7FF",
    "dark_bg": "#3737C3",
    # Text and UI
    "text_primary": "#1A1A1A",
    "text_secondary": "#4B5563",
    "text_muted": "#6B7280",
    "grid": "#E5E7EB",
    "spine": "#D1D5DB",
    # Markers
    "optimal_marker": "#F55B53",
    "constraint_line": "#9CA3AF",
}

# Channel-specific colors (maps to brand secondary palette)
CHANNEL_COLORS = {
    "google": "#5555F2",  # Blurple - primary gets the hero color
    "meta": "#8A57F0",  # Purple
    "tiktok": "#F55B53",  # Red
    "reddit": "#F5CF22",  # Yellow
    "x": "#2FF579",  # Green
}

# Categorical palette as list (for seaborn)
PALETTE = ["#5555F2", "#8A57F0", "#F55B53", "#F5CF22", "#2FF579"]

# =============================================================================
# ANNOTATION BOX STYLES
# =============================================================================

BBOX_STYLES = {
    "neutral": {
        "boxstyle": "round,pad=0.3",
        "facecolor": "#F5F7FF",
        "edgecolor": "#D1D5DB",
        "alpha": 0.95,
        "linewidth": 0.5,
    },
    "success": {
        "boxstyle": "round,pad=0.3",
        "facecolor": "#ECFDF5",
        "edgecolor": "#2FF579",
        "alpha": 0.95,
        "linewidth": 0.5,
    },
    "info": {
        "boxstyle": "round,pad=0.3",
        "facecolor": "#EEF2FF",
        "edgecolor": "#5555F2",
        "alpha": 0.95,
        "linewidth": 0.5,
    },
    "warning": {
        "boxstyle": "round,pad=0.3",
        "facecolor": "#FFFBEB",
        "edgecolor": "#F5CF22",
        "alpha": 0.95,
        "linewidth": 0.5,
    },
}

# =============================================================================
# MATPLOTLIB RC PARAMS
# =============================================================================

RC_PARAMS = {
    # Figure
    "figure.facecolor": "#FFFFFF",
    "figure.titlesize": 16,
    "figure.titleweight": 600,
    # Axes
    "axes.facecolor": "#FFFFFF",
    "axes.edgecolor": "#D1D5DB",
    "axes.linewidth": 0.8,
    "axes.titlesize": 13,
    "axes.titleweight": 500,
    "axes.labelsize": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
    # Grid
    "axes.grid": True,
    "grid.color": "#E5E7EB",
    "grid.linewidth": 0.4,
    "grid.alpha": 0.7,
    # Ticks
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    # Legend
    "legend.fontsize": 9,
    "legend.frameon": True,
    "legend.facecolor": "#FFFFFF",
    "legend.edgecolor": "#E5E7EB",
    "legend.framealpha": 0.95,
    # Font
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
    # Saving
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.facecolor": "#FFFFFF",
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def apply_style():
    """Apply Gamesight publication-quality style globally."""
    plt.rcParams.update(RC_PARAMS)
    sns.set_palette(PALETTE)


def get_channel_color(channel):
    return CHANNEL_COLORS.get(channel.lower(), COLORS["primary"])


def get_channel_colors(channels):
    """Get list of colors for multiple channels."""
    return [get_channel_color(ch) for ch in channels]


def get_bbox(style="neutral"):
    """Get annotation box properties"""
    return BBOX_STYLES.get(style, BBOX_STYLES["neutral"]).copy()


def format_currency(value: float, decimals: int = 0):
    """Format currency with K/M suffix for readability"""
    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:.{decimals}f}M"
    elif abs(value) >= 1_000:
        return f"${value / 1_000:.{decimals}f}K"
    else:
        return f"${value:.{decimals}f}"


def format_currency_precise(value: float):
    """Format currency with commas and cents (e.g., $42,123.45)"""
    return f"${value:,.2f}"


def format_channel_name(name):
    special_cases = {"x": "X", "tiktok": "TikTok"}
    lower = name.lower()
    return special_cases.get(lower, name.title())
