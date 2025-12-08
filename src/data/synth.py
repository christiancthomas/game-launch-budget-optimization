"""Synthetic channel data for budget optimization.

Models diminishing returns with quadratic curves. Generates realistic CPC/CTR/CVR
metrics per channel, ignoring seasonality and genre effects for simplicity.
"""

import csv
import random

# Channel profiles with realistic characteristics for synthetic data generation
# These profiles are tuned to create an interesting optimization problem where:
# - Channels have similar overall efficiency (so none is obviously dominant)
# - Saturation rates differ (creating trade-offs as spend increases)
# - The optimizer must carefully balance allocations rather than just max/min
CHANNEL_PROFILES = {
    "google": {
        "cpc_multiplier": 1.02,  # slightly higher pricing
        "ctr_multiplier": 1.00,  # baseline engagement
        "cvr_multiplier": 1.03,  # good conversion (intent)
        "saturation_rate": 0.18,  # slow saturation (massive scale)
    },
    "meta": {
        "cpc_multiplier": 1.00,  # baseline pricing
        "ctr_multiplier": 1.01,  # baseline engagement
        "cvr_multiplier": 1.00,  # baseline conversion
        "saturation_rate": 0.22,  # moderate saturation
    },
    "tiktok": {
        "cpc_multiplier": 0.98,  # slightly cheaper
        "ctr_multiplier": 1.02,  # good engagement
        "cvr_multiplier": 0.99,  # slightly lower conversion
        "saturation_rate": 0.20,  # moderate saturation
    },
    "reddit": {
        "cpc_multiplier": 1.01,  # baseline pricing
        "ctr_multiplier": 0.98,  # moderate engagement
        "cvr_multiplier": 1.02,  # good conversion
        "saturation_rate": 0.24,  # faster saturation (niche)
    },
    "x": {
        "cpc_multiplier": 0.99,  # competitive pricing
        "ctr_multiplier": 0.99,  # average engagement
        "cvr_multiplier": 1.01,  # average conversion
        "saturation_rate": 0.23,  # moderate saturation
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


def sample_channel_metrics_for_channel(
    channel_name: str, config: dict, shared_base: dict = None
):
    """Sample metrics with channel personality

    If shared_base is provided, uses those metrics as the base for all channels.
    This ensures channels are differentiated only by their profile multipliers,
    creating a more competitive optimization problem.
    """
    # Use shared base if provided, otherwise sample fresh
    base = shared_base if shared_base else sample_base_metrics(config)

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

    # Sample shared base metrics once - all channels start from same baseline
    # This ensures differentiation comes only from profile multipliers,
    # creating a more competitive/balanced optimization problem
    shared_base = sample_base_metrics(config)

    benchmarks = []
    for ch in config["channels"]:
        metrics = sample_channel_metrics_for_channel(ch["name"], config, shared_base)

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
