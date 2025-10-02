"""
plots.py holds the functions for visualizing budget optimization results.
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional

from src.features.curves import quad_conversions, quad_grad


def plot_allocation_breakdown(
    results_df: pd.DataFrame,
    title: str = "Optimal Budget Allocation",
    save_path: Optional[str] = None,
    figsize: tuple = (10, 6),
):
    """
    Generates a bar chart showing optimal spend allocation across channels.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    channels = results_df["channel"]
    spends = results_df["optimal_spend"]
    cpas = results_df["cost_per_acquisition"]

    # Left: Budget allocation
    bars1 = ax1.bar(channels, spends, color="steelblue", alpha=0.7)
    ax1.set_title("Budget Allocation by Channel")
    ax1.set_ylabel("Spend ($)")
    ax1.set_xlabel("Channel")
    ax1.tick_params(axis="x", rotation=45)

    # Add spend labels on bars
    for bar, spend in zip(bars1, spends):
        height = bar.get_height()
        ax1.text(
            bar.get_x() + bar.get_width() / 2.0,
            height,
            f"${spend:,.0f}",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    # Right: CPA comparison
    bars2 = ax2.bar(channels, cpas, color="coral", alpha=0.7)
    ax2.set_title("Cost Per Acquisition (CPA)")
    ax2.set_ylabel("CPA ($)")
    ax2.set_xlabel("Channel")
    ax2.tick_params(axis="x", rotation=45)

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
        )

    plt.suptitle(title, fontsize=14, fontweight="bold")
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")

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
    # Merge dataframes to get all needed info
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

        # Generate spend range for curve
        min_spend = row["min_spend"]
        max_spend = row["max_spend"]
        spend_range = np.linspace(min_spend, max_spend, 100)

        # Calculate conversions curve
        conversions = [
            quad_conversions(s, row["curve_a"], row["curve_b"]) for s in spend_range
        ]

        # Plot curve
        ax.plot(spend_range, conversions, "b-", linewidth=2, alpha=0.7)

        # Mark optimal point
        optimal_spend = row["optimal_spend"]
        optimal_conversions = row["predicted_conversions"]
        ax.scatter(
            [optimal_spend],
            [optimal_conversions],
            color="red",
            s=100,
            zorder=5,
            label="Optimal",
        )

        # Mark min/max constraints
        min_conversions = quad_conversions(min_spend, row["curve_a"], row["curve_b"])
        max_conversions = quad_conversions(max_spend, row["curve_a"], row["curve_b"])
        ax.axvline(min_spend, color="gray", linestyle="--", alpha=0.5)
        ax.axvline(max_spend, color="gray", linestyle="--", alpha=0.5)

        # Mark constraint points on the curve
        ax.scatter(
            [min_spend], [min_conversions], color="gray", s=50, alpha=0.7, marker="s"
        )
        ax.scatter(
            [max_spend], [max_conversions], color="gray", s=50, alpha=0.7, marker="s"
        )

        ax.set_title(f"{row['channel'].title()}")
        ax.set_xlabel("Spend ($)")
        ax.set_ylabel("Conversions")
        ax.grid(True, alpha=0.3)

        # Add efficiency annotation
        cpa = row["cost_per_acquisition"]
        ax.text(
            0.05,
            0.95,
            f"CPA: ${cpa:.0f}",
            transform=ax.transAxes,
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
        )

    # Hide empty subplots
    for j in range(i + 1, len(axes)):
        axes[j].set_visible(False)

    plt.suptitle(title, fontsize=14, fontweight="bold")
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")

    plt.show()


def plot_efficiency_analysis(
    benchmarks_df: pd.DataFrame,
    results_df: pd.DataFrame,
    title: str = "Channel Efficiency Analysis",
    save_path: Optional[str] = None,
    figsize: tuple = (10, 6),
):
    """
    Efficiency scatter plot showing initial performance vs optimal allocation to show
    why certain channels got more/less budget. Helps us identify characteristics
    driving optimization decisions.
    """
    merged = pd.merge(benchmarks_df, results_df, on="channel")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    # Left: Initial efficiency (curve_a) vs allocation
    ax1.scatter(
        merged["curve_a"],
        merged["optimal_spend"],
        s=100,
        alpha=0.7,
        c=merged["cost_per_acquisition"],
        cmap="RdYlBu_r",
    )

    for _, row in merged.iterrows():
        ax1.annotate(
            row["channel"],
            (row["curve_a"], row["optimal_spend"]),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=9,
        )

    ax1.set_xlabel("Initial Efficiency (curve_a)")
    ax1.set_ylabel("Optimal Spend ($)")
    ax1.set_title("Efficiency vs Allocation")
    ax1.grid(True, alpha=0.3)

    # Right: CPA vs Conversions
    ax2.scatter(
        merged["predicted_conversions"],
        merged["cost_per_acquisition"],
        s=merged["optimal_spend"] / 200,
        alpha=0.7,
        c=range(len(merged)),
        cmap="Set3",
    )

    for _, row in merged.iterrows():
        ax2.annotate(
            row["channel"],
            (row["predicted_conversions"], row["cost_per_acquisition"]),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=9,
        )

    ax2.set_xlabel("Predicted Conversions")
    ax2.set_ylabel("Cost Per Acquisition ($)")
    ax2.set_title("Performance Trade-offs")
    ax2.grid(True, alpha=0.3)

    # Add note about bubble size
    ax2.text(
        0.05,
        0.95,
        "Bubble size = Spend",
        transform=ax2.transAxes,
        verticalalignment="top",
        bbox=dict(boxstyle="round", facecolor="lightblue", alpha=0.5),
    )

    plt.suptitle(title, fontsize=14, fontweight="bold")
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")

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
    At optimality, marginal ROI should be ~equal across channels
    (subject to constraints). Should validate that the optimization
    worked correctly.

    Math:
        Marginal ROI = a - 2*b*spend (derivative of quadratic curve)
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

    bars = ax.barh(
        merged_sorted["channel"],
        merged_sorted["marginal_roi"],
        color="lightgreen",
        alpha=0.7,
    )

    ax.set_xlabel("Marginal ROI (conversions per $)")
    ax.set_ylabel("Channel")
    ax.set_title(title)
    ax.grid(True, alpha=0.3, axis="x")

    # Add ROI values as labels
    for bar, roi in zip(bars, merged_sorted["marginal_roi"]):
        width = bar.get_width()
        ax.text(
            width,
            bar.get_y() + bar.get_height() / 2,
            f"{roi:.4f}",
            ha="left",
            va="center",
            fontsize=9,
        )

    # Add note about optimization theory
    ax.text(
        0.02,
        0.98,
        "At optimality, marginal ROI should be ~equal\n\
(subject to min/max constraints)",
        transform=ax.transAxes,
        verticalalignment="top",
        bbox=dict(boxstyle="round", facecolor="yellow", alpha=0.3),
    )

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")

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

    print("Generating visualization dashboard...")

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

    # Summary stats for CLI output
    total_budget = results_df["optimal_spend"].sum()
    total_conversions = results_df["predicted_conversions"].sum()
    avg_cpa = total_budget / total_conversions if total_conversions > 0 else 0

    print("\nOPTIMIZATION SUMMARY:")
    print(f"   Total Budget: ${total_budget:,.0f}")
    print(f"   Total Conversions: {total_conversions:,.0f}")
    print(f"   Portfolio CPA: ${avg_cpa:.0f}")
    print(f"   Channels Optimized: {len(results_df)}")


def plot_simple_allocation_bar(
    results_df: pd.DataFrame,
    title: str = "Budget Allocation",
    save_path: Optional[str] = None,
    figsize: tuple = (8, 5),
):
    """
    Simple bar chart for quick allocation overview.
    """
    plt.figure(figsize=figsize)

    bars = plt.bar(
        results_df["channel"], results_df["optimal_spend"], color="steelblue", alpha=0.7
    )

    plt.title(title, fontsize=14, fontweight="bold")
    plt.xlabel("Channel")
    plt.ylabel("Optimal Spend ($)")
    plt.xticks(rotation=45)

    # Add spend labels
    for bar, spend in zip(bars, results_df["optimal_spend"]):
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2.0,
            height,
            f"${spend:,.0f}",
            ha="center",
            va="bottom",
        )

    plt.grid(True, alpha=0.3, axis="y")
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")

    plt.show()
