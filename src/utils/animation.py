"""Animation utilities for creating GIFs from optimization data

There is a bunch of really finicky matplotlib and other data viz code
here to ensure consistent and high-quality rendering across frames.
"""

import warnings
import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend for consistent rendering

import matplotlib.pyplot as plt  # noqa: E402

# Suppress tight_layout warnings for gridspec figures
warnings.filterwarnings("ignore", message=".*tight_layout.*", category=UserWarning)
import numpy as np  # noqa: E402
from io import BytesIO  # noqa: E402

import imageio.v2 as imageio  # noqa: E402
from PIL import Image  # noqa: E402

from src.features.curves import quad_grad, quad_conversions  # noqa: E402
from src.viz.style import (  # noqa: E402
    apply_style,
    COLORS,
    get_channel_color,
    get_bbox,
    format_channel_name,
    format_currency,
    format_currency_precise,
)


def create_convergence_gif(
    history: dict,
    benchmarks: list[dict],
    save_path: str = "optimization_convergence.gif",
    fps: int = 5,
    max_frames: int = None,
):
    """
    Animated GIF of optimization convergence for README demos.

    Shows marginal ROI equalization across channels as the solver
    explores toward optimal allocation. Set max_frames to subsample.
    """
    if not history or "iteration" not in history:
        print("No history data - skipping GIF generation")
        return

    iterations = history["iteration"]
    n_iterations = len(iterations)

    frame_indices = _get_frame_indices(n_iterations, max_frames)

    frames = []
    for idx in frame_indices:
        frame = _render_frame(history, benchmarks, idx)
        frames.append(frame)

    # Pause at end so viewer can see final converged state
    duration = 1000 / fps
    durations = [duration] * len(frames)
    durations[-1] = 2000

    imageio.mimsave(save_path, frames, duration=durations, loop=0)


def _get_frame_indices(n_iterations: int, max_frames: int = None):
    """Figure out which iterations to render as frames."""
    if max_frames is None or max_frames >= n_iterations:
        return list(range(n_iterations))

    # Subsample evenly
    step = n_iterations / max_frames
    indices = [int(i * step) for i in range(max_frames)]

    # Always include the last frame
    if indices[-1] != n_iterations - 1:
        indices[-1] = n_iterations - 1

    return indices


def _render_frame(history: dict, benchmarks: list[dict], up_to_idx: int):
    """Render a single frame showing state up to iteration index."""
    iterations = history["iteration"][: up_to_idx + 1]
    objectives = history["objective"][: up_to_idx + 1]

    # Track marginal ROI - shows how optimizer equalizes returns across channels
    marginal_rois = {}
    for bench in benchmarks:
        ch_name = bench["channel"]
        spend_key = f"spend_{ch_name}"
        spends = history[spend_key][: up_to_idx + 1]

        rois = [quad_grad(s, bench["curve_a"], bench["curve_b"]) for s in spends]
        marginal_rois[ch_name] = rois

    # Apply Gamesight style
    apply_style()

    fig = plt.figure(figsize=(12, 8), dpi=100)
    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)

    # Top left: Objective progress
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.plot(
        iterations,
        objectives,
        linewidth=2.5,
        color=COLORS["primary"],
        marker="o",
        markersize=4,
    )
    ax1.set_xlabel("Iteration")
    ax1.set_ylabel("Total Conversions")
    ax1.set_title("Objective Function Progress")
    ax1.grid(True, alpha=0.4)

    # Highlight current point
    ax1.scatter(
        [iterations[-1]],
        [objectives[-1]],
        color=COLORS["red"],
        s=150,
        zorder=5,
        edgecolors="white",
        linewidth=2,
    )

    if len(objectives) > 1:
        improvement = objectives[-1] - objectives[0]
        ax1.text(
            0.05,
            0.95,
            f"Gain: {improvement:,.0f} conv\n"
            f"Iter: {iterations[-1]}/{history['iteration'][-1]}",
            transform=ax1.transAxes,
            verticalalignment="top",
            fontsize=9,
            bbox=get_bbox("success"),
        )

    # Top right: Marginal ROI convergence (KKT optimality condition)
    ax2 = fig.add_subplot(gs[0, 1])

    for ch_name, rois in marginal_rois.items():
        ch_color = get_channel_color(ch_name)
        ax2.plot(
            iterations,
            rois,
            linewidth=2,
            label=format_channel_name(ch_name),
            color=ch_color,
            marker="o",
            markersize=3,
        )
        ax2.scatter(
            [iterations[-1]],
            [rois[-1]],
            color=ch_color,
            s=100,
            zorder=5,
            edgecolors="white",
            linewidth=1.5,
        )

    ax2.set_xlabel("Iteration")
    ax2.set_ylabel("Marginal ROI (conv/$)")
    ax2.set_title("Marginal ROI Convergence")
    ax2.legend(loc="best", fontsize=8)
    ax2.grid(True, alpha=0.4)

    ax2.text(
        0.98,
        0.02,
        "At optimality: marginal ROIs equalize\n(KKT condition)",
        transform=ax2.transAxes,
        ha="right",
        va="bottom",
        fontsize=8,
        bbox=get_bbox("warning"),
    )

    # Bottom: Channel allocation evolution
    ax3 = fig.add_subplot(gs[1, :])

    channel_keys = [k for k in history.keys() if k.startswith("spend_")]

    for ch_key in channel_keys:
        channel_name = ch_key.replace("spend_", "")
        ch_color = get_channel_color(channel_name)
        spend_history = history[ch_key][: up_to_idx + 1]
        ax3.plot(
            iterations,
            spend_history,
            linewidth=2,
            label=format_channel_name(channel_name),
            color=ch_color,
            marker="o",
            markersize=3,
        )

        ax3.scatter(
            [iterations[-1]],
            [spend_history[-1]],
            color=ch_color,
            s=100,
            zorder=5,
            edgecolors="white",
            linewidth=1.5,
        )

    ax3.set_xlabel("Iteration")
    ax3.set_ylabel("Channel Spend")
    ax3.set_title("Budget Allocation Evolution")
    ax3.legend(loc="center left", bbox_to_anchor=(1, 0.5), fontsize=9)
    ax3.grid(True, alpha=0.4)

    plt.suptitle(
        f"Optimization Convergence (Iteration {iterations[-1]})",
        fontsize=16,
        fontweight="semibold",
    )

    # Use tight_layout with fixed padding for consistent frame dimensions
    plt.tight_layout(rect=[0, 0, 0.95, 0.95])

    # Use PIL to ensure consistent frame dimensions across iterations
    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=100, facecolor="white", bbox_inches=None)
    buf.seek(0)

    pil_img = Image.open(buf)

    # Force consistent dimensions by resizing to standard size
    target_size = (1200, 800)
    pil_img = pil_img.resize(target_size, Image.Resampling.LANCZOS)

    img = np.array(pil_img.convert("RGB"))

    buf.close()
    plt.close(fig)

    return img


def create_budget_race_gif(
    history,
    benchmarks,
    save_path="budget_race.gif",
    fps=15,
    max_frames=None,  # Use all iterations
    interpolate_frames=3,  # ~3 iterations/sec at 15fps
):
    """
    Animated bar chart race showing budget reallocation. Shows
    the optimization journey as a bar chart race - bars grow/shrink
    and reorder as the solver finds the optimal allocation!

    - history: Optimization history dict with spend_* keys
    - benchmarks: Channel benchmark data for conversions calculation
    - save_path: Output GIF path
    - fps: Frames per second
    - max_frames: Max keyframes to use (will interpolate between)
    - interpolate_frames: Number of interpolated frames between keyframes
    """
    if not history or "iteration" not in history:
        print("No history data - skipping budget race GIF generation")
        return

    n_iterations = len(history["iteration"])
    keyframe_indices = _get_frame_indices(n_iterations, max_frames)

    # Build interpolated frame data
    all_frame_data = _interpolate_budget_race_frames(
        history, benchmarks, keyframe_indices, interpolate_frames
    )

    frames = []
    for frame_data in all_frame_data:
        frame = _render_budget_race_frame(frame_data, benchmarks)
        frames.append(frame)

    # Pause at end so viewer can see final converged state
    duration = 1000 / fps
    durations = [duration] * len(frames)
    durations[-1] = 2500  # 2.5s pause at end

    imageio.mimsave(save_path, frames, duration=durations, loop=0)


def _interpolate_budget_race_frames(
    history: dict,
    benchmarks: list[dict],
    keyframe_indices: list[int],
    interpolate_frames: int,
):
    """Generate interpolated frame data for smooth budget race animation."""
    channel_names = [b["channel"] for b in benchmarks]
    all_frames = []

    def get_y_positions(spends):
        """Get y-position (rank) for each channel based on spend (descending).
        Uses alphabetical order as tiebreaker when spends are within tolerance."""
        tolerance = 100  # Treat spends within $100 as equal for ordering
        sorted_channels = sorted(
            channel_names,
            key=lambda c: (
                -round(spends[c] / tolerance),
                c,
            ),  # bucket by tolerance, then alpha
        )
        return {ch: rank for rank, ch in enumerate(sorted_channels)}

    for i, idx in enumerate(keyframe_indices):
        # Get current keyframe data
        current_spends = {ch: history[f"spend_{ch}"][idx] for ch in channel_names}
        current_iteration = history["iteration"][idx]

        # Calculate y-positions based on current spend ranking
        current_y = get_y_positions(current_spends)

        # Calculate conversions for this state
        current_conversions = sum(
            quad_conversions(current_spends[b["channel"]], b["curve_a"], b["curve_b"])
            for b in benchmarks
        )

        if i < len(keyframe_indices) - 1:
            # Interpolate to next keyframe
            next_idx = keyframe_indices[i + 1]
            next_spends = {ch: history[f"spend_{ch}"][next_idx] for ch in channel_names}
            next_iteration = history["iteration"][next_idx]
            next_y = get_y_positions(next_spends)

            for interp in range(interpolate_frames + 1):
                t = interp / (interpolate_frames + 1)

                # Linear interpolation of spends
                interp_spends = {
                    ch: current_spends[ch] + t * (next_spends[ch] - current_spends[ch])
                    for ch in channel_names
                }

                # Linear interpolation of y-positions (smooth sliding)
                interp_y = {
                    ch: current_y[ch] + t * (next_y[ch] - current_y[ch])
                    for ch in channel_names
                }

                interp_iteration = int(
                    current_iteration + t * (next_iteration - current_iteration)
                )

                # Recalculate conversions for interpolated state
                interp_conversions = sum(
                    quad_conversions(
                        interp_spends[b["channel"]], b["curve_a"], b["curve_b"]
                    )
                    for b in benchmarks
                )

                all_frames.append(
                    {
                        "spends": interp_spends,
                        "y_positions": interp_y,
                        "conversions": interp_conversions,
                        "iteration": interp_iteration,
                        "total_iterations": history["iteration"][-1],
                    }
                )
        else:
            # Last keyframe - no interpolation needed
            all_frames.append(
                {
                    "spends": current_spends,
                    "y_positions": current_y,
                    "conversions": current_conversions,
                    "iteration": current_iteration,
                    "total_iterations": history["iteration"][-1],
                }
            )

    return all_frames


def _render_budget_race_frame(frame_data: dict, benchmarks: list[dict]):
    """Render a single budget race animation frame (horizontal bar chart race)"""
    apply_style()

    spends = frame_data["spends"]
    y_positions = frame_data["y_positions"]
    conversions = frame_data["conversions"]
    iteration = frame_data["iteration"]
    total_iterations = frame_data["total_iterations"]

    # Get channel list (order doesn't matter since we use interpolated y-positions)
    channel_names = list(spends.keys())

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6), dpi=100)

    # Fixed x-axis range for consistent animation
    max_spend = 110000  # Slightly above max possible spend

    # Grid behind bars (fix grid line visibility issue)
    ax.set_axisbelow(True)
    ax.grid(axis="x", alpha=0.4, zorder=0)

    # Draw horizontal bars using interpolated y-positions for smooth sliding
    bar_height = 0.7

    for channel in channel_names:
        spend = spends[channel]
        y_pos = y_positions[channel]  # Use interpolated y-position
        color = get_channel_color(channel)

        # Draw bar with zorder to render above grid
        ax.barh(
            y_pos,
            spend,
            height=bar_height,
            color=color,
            edgecolor="white",
            linewidth=1,
            zorder=3,
        )

        # Channel label on left (inside bar if wide enough, outside if not)
        label = format_channel_name(channel)
        if spend > max_spend * 0.15:
            ax.text(
                spend - max_spend * 0.02,
                y_pos,
                label,
                va="center",
                ha="right",
                fontsize=12,
                fontweight="bold",
                color="white",
            )
        else:
            ax.text(
                spend + max_spend * 0.01,
                y_pos,
                label,
                va="center",
                ha="left",
                fontsize=12,
                fontweight="bold",
                color=color,
            )

        # Spend value at end of bar
        ax.text(
            (
                spend + max_spend * 0.01
                if spend > max_spend * 0.15
                else spend + max_spend * 0.12
            ),
            y_pos,
            format_currency_precise(spend),
            va="center",
            ha="left",
            fontsize=10,
            color=COLORS["text_secondary"],
        )

    # Style the chart
    ax.set_xlim(0, max_spend)
    ax.set_ylim(-0.5, len(channel_names) - 0.5)
    ax.invert_yaxis()  # Largest at top
    ax.set_yticks([])
    ax.set_xlabel("Budget Allocation", fontsize=12)

    # Format x-axis with currency
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: format_currency(x)))

    # Add iteration counter and conversions
    ax.text(
        0.98,
        0.02,
        f"Iteration {iteration}/{total_iterations}",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=12,
        fontweight="semibold",
        color=COLORS["text_secondary"],
    )

    ax.text(
        0.98,
        0.98,
        f"{conversions:,.0f} conversions",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=14,
        fontweight="bold",
        color=COLORS["primary"],
        bbox=get_bbox("success"),
    )

    # Title
    ax.set_title(
        "Budget Optimization in Action",
        fontsize=16,
        fontweight="semibold",
        pad=15,
    )

    plt.tight_layout()

    # Render to image with consistent dimensions
    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=100, facecolor="white", bbox_inches="tight")
    buf.seek(0)

    pil_img = Image.open(buf)
    target_size = (1000, 600)
    pil_img = pil_img.resize(target_size, Image.Resampling.LANCZOS)

    img = np.array(pil_img.convert("RGB"))

    buf.close()
    plt.close(fig)

    return img
