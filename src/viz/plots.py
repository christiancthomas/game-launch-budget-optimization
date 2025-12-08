"""
Visualization functions for budget optimization results.
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional

from src.features.curves import quad_conversions, quad_grad
from src.viz.style import (
    apply_style,
    COLORS,
    get_channel_color,
    get_channel_colors,
    get_bbox,
    format_currency,
    format_channel_name,
)

# Apply standardized publication style
apply_style()


def plot_allocation_breakdown(
    results_df: pd.DataFrame,
    title: str = "Optimal Budget Allocation",
    save_path: Optional[str] = None,
    figsize: tuple = (10, 6),
):
    """
    Bar chart showing optimal spend allocation across channels.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    channels = [format_channel_name(ch) for ch in results_df["channel"]]
    spends = results_df["optimal_spend"]
    cpas = results_df["cost_per_acquisition"]
    bar_colors = get_channel_colors(results_df["channel"])

    # Left: Budget allocation
    ax1.set_axisbelow(True)  # Grid behind bars
    bars1 = ax1.bar(channels, spends, color=bar_colors, zorder=3)
    ax1.set_title("Budget Allocation by Channel")
    ax1.set_ylabel("Spend")
    ax1.set_xlabel("Channel")
    ax1.tick_params(axis="x", rotation=45)
    ax1.grid(axis="y", alpha=0.5, zorder=0)

    # Add spend labels on bars
    for bar, spend in zip(bars1, spends):
        height = bar.get_height()
        ax1.text(
            bar.get_x() + bar.get_width() / 2.0,
            height,
            format_currency(spend),
            ha="center",
            va="bottom",
            fontsize=9,
            color=COLORS["text_secondary"],
        )

    # Right: CPA comparison
    ax2.set_axisbelow(True)
    bars2 = ax2.bar(channels, cpas, color=bar_colors, zorder=3)
    ax2.set_title("Cost Per Acquisition (CPA)")
    ax2.set_ylabel("CPA")
    ax2.set_xlabel("Channel")
    ax2.tick_params(axis="x", rotation=45)
    ax2.grid(axis="y", alpha=0.5, zorder=0)

    # Add CPA labels on bars
    for bar, cpa in zip(bars2, cpas):
        height = bar.get_height()
        ax2.text(
            bar.get_x() + bar.get_width() / 2.0,
            height,
            f"${cpa:.0f}",
            ha="center",
            va="bottom",
            fontsize=9,
            color=COLORS["text_secondary"],
        )

    plt.suptitle(title, fontsize=14, fontweight="semibold")
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        plt.close()
    else:
        plt.show()


def plot_channel_curves(
    benchmarks_df: pd.DataFrame,
    results_df: pd.DataFrame,
    title: str = "Channel Response Curves",
    save_path: Optional[str] = None,
    figsize: tuple = (12, 8),
):
    """
    Response curves showing conversions vs spend for each channel. Intended to
    show diminishing returns and highlights optimal spend points.
    Helps to visualize why the optimizer chose specific allocations.
    """
    merged = pd.merge(benchmarks_df, results_df, on="channel")

    n_channels = len(merged)
    cols = 2
    rows = (n_channels + 1) // cols

    fig, axes = plt.subplots(rows, cols, figsize=figsize)
    if n_channels == 1:
        axes = [axes]
    elif rows == 1:
        axes = axes.reshape(1, -1)
    axes = axes.flatten()

    for i, (_, row) in enumerate(merged.iterrows()):
        ax = axes[i]
        channel_name = row["channel"]
        channel_color = get_channel_color(channel_name)

        # Generate spend range for curve
        min_spend = row["min_spend"]
        max_spend = row["max_spend"]
        spend_range = np.linspace(min_spend, max_spend, 100)

        # Calculate conversions curve
        conversions = [
            quad_conversions(s, row["curve_a"], row["curve_b"]) for s in spend_range
        ]

        # Plot curve with channel color
        ax.plot(spend_range, conversions, color=channel_color, linewidth=2.5, alpha=0.9)

        # Mark optimal point
        optimal_spend = row["optimal_spend"]
        optimal_conversions = row["predicted_conversions"]
        ax.scatter(
            [optimal_spend],
            [optimal_conversions],
            color=COLORS["optimal_marker"],
            s=100,
            zorder=5,
            edgecolors="white",
            linewidth=1.5,
            label="Optimal",
        )

        # Mark min/max constraints
        min_conversions = quad_conversions(min_spend, row["curve_a"], row["curve_b"])
        max_conversions = quad_conversions(max_spend, row["curve_a"], row["curve_b"])
        ax.axvline(
            min_spend, color=COLORS["constraint_line"], linestyle="--", alpha=0.6
        )
        ax.axvline(
            max_spend, color=COLORS["constraint_line"], linestyle="--", alpha=0.6
        )

        # Mark constraint points on the curve
        ax.scatter(
            [min_spend],
            [min_conversions],
            color=COLORS["constraint_line"],
            s=40,
            alpha=0.7,
            marker="s",
        )
        ax.scatter(
            [max_spend],
            [max_conversions],
            color=COLORS["constraint_line"],
            s=40,
            alpha=0.7,
            marker="s",
        )

        ax.set_title(format_channel_name(channel_name))
        ax.set_xlabel("Spend")
        ax.set_ylabel("Conversions")
        ax.grid(True, alpha=0.4)

        # Add CPA annotation with new styling
        cpa = row["cost_per_acquisition"]
        ax.text(
            0.05,
            0.95,
            f"CPA: ${cpa:.0f}",
            transform=ax.transAxes,
            verticalalignment="top",
            fontsize=9,
            bbox=get_bbox("neutral"),
        )

    # Hide empty subplots
    for j in range(i + 1, len(axes)):
        axes[j].set_visible(False)

    plt.suptitle(title, fontsize=14, fontweight="semibold")
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        plt.close()
    else:
        plt.show()


def plot_efficiency_analysis(
    benchmarks_df: pd.DataFrame,
    results_df: pd.DataFrame,
    title: str = "Channel Efficiency Analysis",
    save_path: Optional[str] = None,
    figsize: tuple = (10, 6),
):
    """
    Efficiency scatter plot showing initial performance vs optimal allocation.
    Identifies characteristics driving optimization decisions.
    """
    merged = pd.merge(benchmarks_df, results_df, on="channel")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    # Left: Initial efficiency (curve_a) vs allocation
    scatter_colors = get_channel_colors(merged["channel"])
    ax1.scatter(
        merged["curve_a"],
        merged["optimal_spend"],
        s=120,
        alpha=0.85,
        c=scatter_colors,
        edgecolors="white",
        linewidth=1,
    )

    for _, row in merged.iterrows():
        ax1.annotate(
            format_channel_name(row["channel"]),
            (row["curve_a"], row["optimal_spend"]),
            xytext=(6, 6),
            textcoords="offset points",
            fontsize=9,
            color=COLORS["text_secondary"],
        )

    ax1.set_xlabel("Initial Efficiency (curve_a)")
    ax1.set_ylabel("Optimal Spend")
    ax1.set_title("Efficiency vs Allocation")
    ax1.grid(True, alpha=0.4)

    # Right: CPA vs Conversions (bubble chart)
    ax2.scatter(
        merged["predicted_conversions"],
        merged["cost_per_acquisition"],
        s=merged["optimal_spend"] / 150,
        alpha=0.75,
        c=scatter_colors,
        edgecolors="white",
        linewidth=1,
    )

    for _, row in merged.iterrows():
        ax2.annotate(
            format_channel_name(row["channel"]),
            (row["predicted_conversions"], row["cost_per_acquisition"]),
            xytext=(6, 6),
            textcoords="offset points",
            fontsize=9,
            color=COLORS["text_secondary"],
        )

    ax2.set_xlabel("Predicted Conversions")
    ax2.set_ylabel("Cost Per Acquisition")
    ax2.set_title("Performance Trade-offs")
    ax2.grid(True, alpha=0.4)

    # Add note about bubble size
    ax2.text(
        0.05,
        0.95,
        "Bubble size = Spend",
        transform=ax2.transAxes,
        verticalalignment="top",
        fontsize=9,
        bbox=get_bbox("info"),
    )

    plt.suptitle(title, fontsize=14, fontweight="semibold")
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        plt.close()
    else:
        plt.show()


def plot_marginal_roi_comparison(
    benchmarks_df: pd.DataFrame,
    results_df: pd.DataFrame,
    title: str = "Marginal ROI at Optimal Allocation",
    save_path: Optional[str] = None,
    figsize: tuple = (10, 5),
):
    """
    Bar chart showing marginal ROI for each channel at optimal spend.

    At optimality, marginal ROI should be roughly equal across channels
    (subject to constraints) - validates that the optimizer worked correctly.

    Math: Marginal ROI = a - 2*b*spend (derivative of quadratic curve)
    """
    merged = pd.merge(benchmarks_df, results_df, on="channel")

    # Calculate marginal ROI at optimal spend
    marginal_rois = []
    for _, row in merged.iterrows():
        roi = quad_grad(row["optimal_spend"], row["curve_a"], row["curve_b"])
        marginal_rois.append(roi)

    merged["marginal_roi"] = marginal_rois

    # Sort by marginal ROI for cleaner chart
    merged_sorted = merged.sort_values("marginal_roi", ascending=True)

    fig, ax = plt.subplots(figsize=figsize)

    # Get channel colors in sorted order
    bar_colors = get_channel_colors(merged_sorted["channel"])
    channel_labels = [format_channel_name(ch) for ch in merged_sorted["channel"]]

    ax.set_axisbelow(True)
    bars = ax.barh(
        channel_labels,
        merged_sorted["marginal_roi"],
        color=bar_colors,
        zorder=3,
    )

    ax.set_xlabel("Marginal ROI (conversions per $)")
    ax.set_ylabel("Channel")
    ax.set_title(title)
    ax.grid(True, alpha=0.4, axis="x", zorder=0)

    # Add ROI values as labels
    for bar, roi in zip(bars, merged_sorted["marginal_roi"]):
        width = bar.get_width()
        ax.text(
            width + 0.0002,
            bar.get_y() + bar.get_height() / 2,
            f"{roi:.4f}",
            ha="left",
            va="center",
            fontsize=9,
            color=COLORS["text_secondary"],
        )

    # Add note about optimization theory
    ax.text(
        0.02,
        0.98,
        "At optimality, marginal ROI should be ~equal\n"
        "(subject to min/max constraints)",
        transform=ax.transAxes,
        verticalalignment="top",
        fontsize=9,
        bbox=get_bbox("warning"),
    )

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        plt.close()
    else:
        plt.show()


def create_full_dashboard(
    benchmarks_path: str,
    results_path: str,
    output_dir: str = "experiments/results/figures",
    show_plots: bool = True,
):
    """
    Generate complete visualization dashboard for optimization results.

    Business logic:
        One-stop shop for all the charts a marketing team needs to understand
        and present the budget allocation recommendations.
    """
    # Load data
    benchmarks_df = pd.read_csv(benchmarks_path)
    results_df = pd.read_csv(results_path)

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Set matplotlib to non-interactive if not showing
    if not show_plots:
        plt.ioff()

    # Generate all charts
    plot_allocation_breakdown(
        results_df, save_path=output_path / "allocation_breakdown.png"
    )

    plot_channel_curves(
        benchmarks_df, results_df, save_path=output_path / "channel_curves.png"
    )

    plot_efficiency_analysis(
        benchmarks_df, results_df, save_path=output_path / "efficiency_analysis.png"
    )

    plot_marginal_roi_comparison(
        benchmarks_df, results_df, save_path=output_path / "marginal_roi_comparison.png"
    )


def plot_simple_allocation_bar(
    results_df: pd.DataFrame,
    title: str = "Budget Allocation",
    save_path: Optional[str] = None,
    figsize: tuple = (8, 5),
):
    """
    Simple bar chart for quick allocation overview.
    """
    fig, ax = plt.subplots(figsize=figsize)

    channels = [format_channel_name(ch) for ch in results_df["channel"]]
    bar_colors = get_channel_colors(results_df["channel"])

    ax.set_axisbelow(True)
    bars = ax.bar(channels, results_df["optimal_spend"], color=bar_colors, zorder=3)

    ax.set_title(title, fontsize=14, fontweight="semibold")
    ax.set_xlabel("Channel")
    ax.set_ylabel("Optimal Spend")
    plt.xticks(rotation=45)

    # Add spend labels
    for bar, spend in zip(bars, results_df["optimal_spend"]):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            height,
            format_currency(spend),
            ha="center",
            va="bottom",
            fontsize=9,
            color=COLORS["text_secondary"],
        )

    ax.grid(True, alpha=0.4, axis="y", zorder=0)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        plt.close()
    else:
        plt.show()


def plot_optimization_convergence(
    history: dict,
    title: str = "Optimization Convergence",
    save_path: Optional[str] = None,
    figsize: tuple = (12, 8),
):
    """
    Visualize the optimization algorithm converging to optimal solution.

    Business logic:
        Shows how the optimizer explores the solution space and settles
        on the best allocation. Demonstrates that we're finding a
        mathematically optimal solution, not just guessing.

    Math:
        Tracks objective function value (total conversions) and constraint
        satisfaction across iterations.
    """
    if not history or "iteration" not in history:
        print("No optimization history available to plot")
        return

    iterations = history["iteration"]
    objectives = history["objective"]
    budget_errors = history["budget_error"]

    # Create 2x2 subplot grid
    fig = plt.figure(figsize=figsize)
    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)

    # Top left: Objective function (conversions) over iterations
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.plot(
        iterations,
        objectives,
        linewidth=2.5,
        color=COLORS["primary"],
        marker="o",
        markersize=4,
        markevery=max(1, len(iterations) // 20),
    )
    ax1.set_xlabel("Iteration")
    ax1.set_ylabel("Total Conversions")
    ax1.set_title("Objective Function Progress")
    ax1.grid(True, alpha=0.4)

    # Add improvement annotation
    if len(objectives) > 1:
        improvement = objectives[-1] - objectives[0]
        ax1.text(
            0.05,
            0.95,
            f"Total gain: {improvement:,.0f} conversions",
            transform=ax1.transAxes,
            verticalalignment="top",
            fontsize=9,
            bbox=get_bbox("success"),
        )

    # Top right: Budget constraint error
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.plot(
        iterations,
        budget_errors,
        linewidth=2.5,
        color=COLORS["red"],
        marker="s",
        markersize=4,
        markevery=max(1, len(iterations) // 20),
    )
    ax2.set_xlabel("Iteration")
    ax2.set_ylabel("Budget Constraint Error")
    ax2.set_title("Constraint Satisfaction")
    ax2.axhline(
        y=0,
        color=COLORS["constraint_line"],
        linestyle="--",
        alpha=0.6,
        label="Perfect balance",
    )
    ax2.grid(True, alpha=0.4)
    ax2.legend(fontsize=8)
    # Format y-axis - use scientific notation only when values are very small
    ax2.yaxis.set_major_formatter(
        plt.FuncFormatter(
            lambda x, _: f"{x:.2e}" if abs(x) > 0 and abs(x) < 0.001 else f"{x:.4f}"
        )
    )

    # Bottom: Channel allocation evolution (multi-line plot)
    ax3 = fig.add_subplot(gs[1, :])

    # Plot spend trajectory for each channel using brand colors
    channel_keys = [k for k in history.keys() if k.startswith("spend_")]

    for ch_key in channel_keys:
        channel_name = ch_key.replace("spend_", "")
        spend_history = history[ch_key]
        channel_color = get_channel_color(channel_name)
        ax3.plot(
            iterations,
            spend_history,
            linewidth=2,
            label=format_channel_name(channel_name),
            color=channel_color,
            marker="o",
            markersize=3,
            markevery=max(1, len(iterations) // 15),
        )

    ax3.set_xlabel("Iteration")
    ax3.set_ylabel("Channel Spend")
    ax3.set_title("Budget Allocation Evolution")
    ax3.legend(loc="center left", bbox_to_anchor=(1, 0.5), fontsize=9)
    ax3.grid(True, alpha=0.4)

    plt.suptitle(title, fontsize=16, fontweight="semibold")

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        plt.close()
    else:
        plt.show()
