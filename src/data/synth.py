"""Synthetic channel data for budget optimization.

Models diminishing returns with quadratic curves. Generates realistic CPC/CTR/CVR
metrics per channel, ignoring seasonality and genre effects for simplicity.
"""

import csv
import random

# Channel profiles with realistic characteristics for synthetic data generation
CHANNEL_PROFILES = {
    "google": {
        "cpc_multiplier": 1.0,  # baseline
        "ctr_multiplier": 2.0,  # very high engagement
        "cvr_multiplier": 2.0,  # strong conversion
        "saturation_rate": 0.2,  # moderate saturation
    },
    "meta": {
        "cpc_multiplier": 1.3,  # decent click cost
        "ctr_multiplier": 1.0,  # good engagement
        "cvr_multiplier": 1.2,  # good conversion
        "saturation_rate": 0.1,  # slower saturation
    },
    "tiktok": {
        "cpc_multiplier": 0.5,  # cheap clicks
        "ctr_multiplier": 1.4,  # high engagement
        "cvr_multiplier": 1.5,  # decent conversion
        "saturation_rate": 0.15,  # slower saturation
    },
    "reddit": {
        "cpc_multiplier": 0.8,  # cheap clicks
        "ctr_multiplier": 1.0,  # moderate engagement
        "cvr_multiplier": 1.2,  # good conversions
        "saturation_rate": 0.25,  # moderate saturation
    },
    "x": {
        "cpc_multiplier": 0.7,  # moderately cheap clicks
        "ctr_multiplier": 1.0,  # moderate engagement
        "cvr_multiplier": 1.0,  # moderate conversion
        "saturation_rate": 0.35,  # high saturation
    },
}


def sample_base_metrics(config: dict):
    """Random metrics from config ranges."""
    synth = config["synth_data"]
    return {
        "cpc": random.uniform(*synth["cpc_range"]),
        "ctr": random.uniform(*synth["ctr_range"]),
        "cvr": random.uniform(*synth["cvr_range"]),
    }


def channel_adjustments(base_metrics: dict, channel_name: str):
    """Apply channel personality multipliers."""

    # Get the personality profile for this channel
    profile = CHANNEL_PROFILES.get(channel_name, {})

    # Apply multipliers to the sampled base metrics
    return {
        "cpc": base_metrics["cpc"] * profile.get("cpc_multiplier", 1.0),
        "ctr": base_metrics["ctr"] * profile.get("ctr_multiplier", 1.0),
        "cvr": base_metrics["cvr"] * profile.get("cvr_multiplier", 1.0),
    }


def sample_channel_metrics_for_channel(channel_name: str, config: dict):
    """Sample metrics with channel personality."""

    # Start with random base metrics
    base = sample_base_metrics(config)

    # Apply this channel's personality
    return channel_adjustments(base, channel_name)


def derive_quad_params(
    cpc: float, ctr: float, cvr: float, max_spend: float, saturation_rate=0.3
):
    """
    Turn funnel metrics into (a,b) curve coefficients.

    Business logic:
        This models simplified diminishing returns — after the saturation point,
        each extra dollar brings in fewer conversions because you start reaching
        lower-quality audiences and face bid competition.

    Math:
        `conversions = (a * spend) - (b * spend²)`
        - 'a' is the initial conversions per dollar (≈ CVR * CTR / CPC)
        - 'b' is the curvature that flattens performance as spend grows

    This is intentionally simple for V1: concave, monotone-increasing in our operating
    range, and easy to optimize with quadratic programming.

    V2 will introduce more complexity.
    """

    # Key mathematical principle: conversions = (a * spend) - (b * spend²)
    a = (ctr * cvr) / cpc  # this is our base efficiency, or performance at low spend

    # Solve: efficiency_at_max = base_efficiency * (1 - saturation_rate)
    # This gives us the 'b' parameter
    b = (a * saturation_rate) / max_spend

    return a, b


def generate_channel_benchmarks(config: dict) -> list[dict]:
    """
    Generate benchmarks for all channels.

    Business logic:
        Create realistic marketing channel performance data that roughly reflects
        real-world differences (Google has higher CPC but better conversion,
        TikTok has cheaper clicks but lower intent, etc.).

    Math:
        For each channel: sample base metrics → apply personality → derive quadratic
        parameters → validate mathematical properties (positive ROI, concavity).

    Output feeds directly into quadratic programming solver.
    """
    random.seed(config["synth_data"]["random_seed"])

    benchmarks = []
    for ch in config["channels"]:
        metrics = sample_channel_metrics_for_channel(ch["name"], config)

        # Get channel-specific saturation rate from profile
        profile = CHANNEL_PROFILES.get(ch["name"], {})
        saturation_rate = profile.get(
            "saturation_rate", 0.3
        )  # Default to 0.3 if not found

        a, b = derive_quad_params(
            metrics["cpc"],
            metrics["ctr"],
            metrics["cvr"],
            ch["max_spend"],
            saturation_rate,
        )

        benchmarks.append(
            {
                "channel": ch["name"],
                "cpc": metrics["cpc"],
                "ctr": metrics["ctr"],
                "cvr": metrics["cvr"],
                "min_spend": ch["min_spend"],
                "max_spend": ch["max_spend"],
                "curve_a": a,
                "curve_b": b,
            }
        )

    return benchmarks


def write_benchmarks_csv(benchmarks: list[dict], output_path: str):
    """Write channel benchmarks to CSV."""
    with open(output_path, "w", newline="") as f:
        if benchmarks:
            writer = csv.DictWriter(f, fieldnames=benchmarks[0].keys())
            writer.writeheader()
            writer.writerows(benchmarks)
