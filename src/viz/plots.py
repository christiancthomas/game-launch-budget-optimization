"""
plots.py holds the functions for visualizing budget optimization results.
"""

import matplotlib.pyplot as plt
import pandas as pd
from typing import Optional


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
        print(f"📊 Saved allocation breakdown to: {save_path}")

    plt.show()


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
        print(f"📊 Saved simple allocation chart to: {save_path}")

    plt.show()
