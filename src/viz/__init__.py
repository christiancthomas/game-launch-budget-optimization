"""Visualization module for budget optimization."""

from src.viz.style import (
    apply_style,
    COLORS,
    CHANNEL_COLORS,
    PALETTE,
    get_channel_color,
    get_channel_colors,
    get_bbox,
    format_currency,
    format_channel_name,
)

from src.viz.plots import (
    plot_allocation_breakdown,
    plot_channel_curves,
    plot_efficiency_analysis,
    plot_marginal_roi_comparison,
    plot_simple_allocation_bar,
    plot_optimization_convergence,
    create_full_dashboard,
)

__all__ = [
    # Style
    "apply_style",
    "COLORS",
    "CHANNEL_COLORS",
    "PALETTE",
    "get_channel_color",
    "get_channel_colors",
    "get_bbox",
    "format_currency",
    "format_channel_name",
    # Plots
    "plot_allocation_breakdown",
    "plot_channel_curves",
    "plot_efficiency_analysis",
    "plot_marginal_roi_comparison",
    "plot_simple_allocation_bar",
    "plot_optimization_convergence",
    "create_full_dashboard",
]
