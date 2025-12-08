"""Animation utilities for creating GIFs from optimization data"""

import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend for consistent rendering

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from io import BytesIO  # noqa: E402

import imageio.v2 as imageio  # noqa: E402
from PIL import Image  # noqa: E402

from src.features.curves import quad_grad  # noqa: E402
from src.viz.style import (  # noqa: E402
    apply_style,
    COLORS,
    get_channel_color,
    get_bbox,
    format_channel_name,
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

    print(f"Generating {len(frame_indices)} frames for convergence GIF...")

    frames = []
    for idx in frame_indices:
        frame = _render_frame(history, benchmarks, idx)
        frames.append(frame)

    # Pause at end so viewer can see final converged state
    duration = 1000 / fps
    durations = [duration] * len(frames)
    durations[-1] = 2000

    imageio.mimsave(save_path, frames, duration=durations, loop=0)

    total_duration = (len(frames) - 1) / fps + 2.0  # Regular frames + 2s pause
    print(f"Convergence GIF saved to: {save_path}")
    print(
        f"   {len(frames)} frames @ {fps} fps + 2s pause = "
        f"{total_duration:.1f}s animation"
    )


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

    # Use PIL to ensure consistent frame dimensions across iterations
    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=100, facecolor="white")
    buf.seek(0)

    pil_img = Image.open(buf)
    img = np.array(pil_img.convert("RGB"))

    buf.close()
    plt.close(fig)

    return img
