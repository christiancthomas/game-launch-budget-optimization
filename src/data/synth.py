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
        "ctr_multiplier": 1.2,  # high engagement
        "cvr_multiplier": 1.5,  # strong conversion
        "saturation_rate": 0.3,  # moderate saturation
    },
    "meta": {
        "cpc_multiplier": 1.0,  # baseline
        "ctr_multiplier": 0.9,  # high engagement
        "cvr_multiplier": 1.1,  # strong conversion
        "saturation_rate": 0.15,  # slow saturation
    },
    "tiktok": {
        "cpc_multiplier": 0.6,  # cheap clicks
        "ctr_multiplier": 1.3,  # high engagement
        "cvr_multiplier": 0.7,  # moderate conversion
        "saturation_rate": 0.2,  # slow saturation
    },
    "reddit": {
        "cpc_multiplier": 0.8,  # cheap clicks
        "ctr_multiplier": 1.1,  # high engagement
        "cvr_multiplier": 1.0,  # moderate conversion
        "saturation_rate": 0.4,  # faster saturation
    },
    "x": {
        "cpc_multiplier": 0.6,  # cheap clicks
        "ctr_multiplier": 1.0,  # moderate engagement
        "cvr_multiplier": 0.5,  # low conversion
        "saturation_rate": 0.6,  # faster saturation
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
    profile = CHANNEL_PROFILES.get(channel_name.lower(), {})

    # Apply multipliers to base metrics
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


def derive_quad_params(cpc: float, ctr: float, cvr: float, max_spend: float):
    """Turn funnel metrics into (a,b) curve coefficients."""

    # Key mathematical principle: conversions = a × spend - b × spend²
    a = (ctr * cvr) / cpc  # this is our base efficiency, or performance at low spend

    # We want the curve to slow down as we approach max_spend
    # Let's say at max_spend, efficiency should drop by some target percentage
    target_eff_drop = 0.3  # 30% efficiency loss at max spend
    # - placeholder value, may end up adjusting

    # Solve: efficiency_at_max = base_efficiency * (1 - target_drop)
    # This gives us the 'b' parameter
    b = (a * target_eff_drop) / max_spend

    return a, b


def generate_channel_benchmarks(config: dict) -> list[dict]:
    """Generate benchmarks for all channels."""
    random.seed(config["synth_data"]["random_seed"])

    benchmarks = []
    for ch in config["channels"]:
        metrics = sample_channel_metrics_for_channel(ch["name"], config)
        a, b = derive_quad_params(
            metrics["cpc"], metrics["ctr"], metrics["cvr"], ch["max_spend"]
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
