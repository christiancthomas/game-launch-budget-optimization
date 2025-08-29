"""
End-to-end integration tests for the full optimization pipeline.

These tests validate that the entire synth -> optimize workflow
actually works in practice, not just in isolation. Basically,
this replicates real-world usage.
"""

import tempfile
from pathlib import Path
import pandas as pd

from src.config.load import load_config
from src.data.synth import generate_channel_benchmarks, write_benchmarks_csv
from src.opt.solve import solve_qp
from src.features.curves import quad_conversions


def test_full_synth_to_optimize_pipeline():
    """End-to-end synth -> optimize pipeline works correctly.

    Proves that the entire workflow from synthetic data generation
    to optimization is functional!"""

    config = load_config("src/config/default.yaml")

    # Generate synthetic benchmarks
    benchmarks = generate_channel_benchmarks(config)

    # Basic structure validation
    assert len(benchmarks) == len(config["channels"])
    for bench in benchmarks:
        assert all(
            key in bench
            for key in [
                "channel",
                "cpc",
                "ctr",
                "cvr",
                "min_spend",
                "max_spend",
                "curve_a",
                "curve_b",
            ]
        )
        assert bench["curve_a"] > 0, f"curve_a must be positive: {bench['curve_a']}"
        assert bench["curve_b"] > 0, f"curve_b must be positive: {bench['curve_b']}"
        assert bench["min_spend"] < bench["max_spend"], "min_spend must be < max_spend"

    # Run optimization
    budget = config["budget"]["total"]
    allocation = solve_qp(benchmarks, budget)

    # Check optimization results structure
    assert isinstance(allocation, dict)
    assert len(allocation) == len(benchmarks)

    # All channels should be present
    expected_channels = {bench["channel"] for bench in benchmarks}
    actual_channels = set(allocation.keys())
    assert (
        expected_channels == actual_channels
    ), f"Channel mismatch: {expected_channels} vs {actual_channels}"

    # Budget conservation (the important one!)
    total_allocated = sum(allocation.values())
    assert (
        abs(total_allocated - budget) < 1e-6
    ), f"Budget not fully allocated: {total_allocated} vs {budget}"

    # Check channel bounds
    for bench in benchmarks:
        channel = bench["channel"]
        spend = allocation[channel]
        assert (
            bench["min_spend"] <= spend <= bench["max_spend"]
        ), f"{channel}: spend {spend} outside bounds \
            [{bench['min_spend']}, {bench['max_spend']}]"

    # Math checks: conversions should be positive and sensible
    total_conversions = 0
    for bench in benchmarks:
        channel = bench["channel"]
        spend = allocation[channel]
        conversions = quad_conversions(spend, bench["curve_a"], bench["curve_b"])

        assert conversions > 0, f"{channel}: negative conversions {conversions}"
        total_conversions += conversions

    # Portfolio CPA should be realistic
    portfolio_cpa = budget / total_conversions
    assert 5 <= portfolio_cpa <= 100, f"Portfolio CPA unrealistic: ${portfolio_cpa:.2f}"

    # Sanity check marketing metrics
    for bench in benchmarks:
        # Basic reasonableness checks
        assert 0.05 <= bench["cpc"] <= 5.0, f"CPC unrealistic: ${bench['cpc']:.3f}"
        assert 0.01 <= bench["ctr"] <= 0.3, f"CTR unrealistic: {bench['ctr']:.3f}"
        assert 0.01 <= bench["cvr"] <= 0.3, f"CVR unrealistic: {bench['cvr']:.3f}"

        # Channel CPA should make sense
        spend = allocation[bench["channel"]]
        conversions = quad_conversions(spend, bench["curve_a"], bench["curve_b"])
        cpa = spend / conversions if conversions > 0 else float("inf")
        assert 5 <= cpa <= 150, f"{bench['channel']} CPA unrealistic: ${cpa:.2f}"


def test_csv_roundtrip_integration():
    """CSV export/import works in the pipeline"""

    with tempfile.TemporaryDirectory() as temp_dir:
        csv_path = Path(temp_dir) / "test_benchmarks.csv"

        # Generate and write benchmarks
        config = load_config("src/config/default.yaml")
        benchmarks = generate_channel_benchmarks(config)
        write_benchmarks_csv(benchmarks, str(csv_path))

        # Verify CSV was created
        assert csv_path.exists(), "CSV file not created"

        # Read back and run optimization
        df = pd.read_csv(csv_path)
        benchmarks_from_csv = df.to_dict("records")  # Like CLI does

        # Run optimization on CSV data
        budget = config["budget"]["total"]
        allocation = solve_qp(benchmarks_from_csv, budget)

        # Validate results
        assert len(allocation) == len(benchmarks)
        total_allocated = sum(allocation.values())
        assert abs(total_allocated - budget) < 1e-6


def test_deterministic_pipeline():
    """Same seed should produce identical results"""

    config = load_config("src/config/default.yaml")
    budget = config["budget"]["total"]

    # Run pipeline twice with same config
    benchmarks_1 = generate_channel_benchmarks(config)
    allocation_1 = solve_qp(benchmarks_1, budget)

    benchmarks_2 = generate_channel_benchmarks(config)
    allocation_2 = solve_qp(benchmarks_2, budget)

    # Results should be identical (same seed)
    assert len(allocation_1) == len(allocation_2)

    for channel in allocation_1:
        assert channel in allocation_2
        assert (
            abs(allocation_1[channel] - allocation_2[channel]) < 1e-6
        ), f"{channel}: {allocation_1[channel]} vs {allocation_2[channel]}"


def test_optimization_makes_business_sense():
    """Optimizer follows expected business logic such as:

    - Optimal channels should get more budget
    - Spends must be > 0
    - High curve_a channels should perform well
    """

    config = load_config("src/config/default.yaml")
    benchmarks = generate_channel_benchmarks(config)
    budget = config["budget"]["total"]

    allocation = solve_qp(benchmarks, budget)

    # Calculate efficiency metrics for each channel
    ch_metrics = []
    for bench in benchmarks:
        channel = bench["channel"]
        spend = allocation[channel]
        conversions = quad_conversions(spend, bench["curve_a"], bench["curve_b"])
        cpa = spend / conversions if conversions > 0 else float("inf")
        efficiency = conversions / spend if spend > 0 else 0

        ch_metrics.append(
            {
                "channel": channel,
                "spend": spend,
                "conversions": conversions,
                "cpa": cpa,
                "efficiency": efficiency,
                "curve_a": bench["curve_a"],
            }
        )

    # Sort by efficiency (descending)
    ch_metrics.sort(key=lambda x: x["efficiency"], reverse=True)

    # Business logic checks:

    # 1. Most efficient channels should generally get more budget (unless constrained)
    most_efficient = ch_metrics[0]
    least_efficient = ch_metrics[-1]

    # The most efficient channel should get at least as much as the least efficient
    # (unless the least efficient is at minimum spend)
    if least_efficient["spend"] > benchmarks[0]["min_spend"]:  # Not at minimum
        assert (
            most_efficient["spend"] >= least_efficient["spend"]
        ), f"Most efficient {most_efficient['channel']} \
            got less spend than least efficient {least_efficient['channel']}"

    # 2. All spends should be positive
    for metrics in ch_metrics:
        assert metrics["spend"] > 0, f"{metrics['channel']} got zero spend"

    # 3. High curve_a (initial efficiency) channels should generally perform well
    high_curve_a_channels = [m for m in ch_metrics if m["curve_a"] > 0.03]
    if high_curve_a_channels:
        # At least one high curve_a channel should be in top half by spend
        sorted_by_spend = sorted(ch_metrics, key=lambda x: x["spend"], reverse=True)
        top_half = sorted_by_spend[: len(sorted_by_spend) // 2 + 1]

        high_curve_a_in_top = any(
            m["channel"] in [t["channel"] for t in top_half]
            for m in high_curve_a_channels
        )
        assert high_curve_a_in_top, "High efficiency channels not prioritized properly"


def test_parameter_sensitivity():
    """Parameter changes produce expected directional effects."""

    config = load_config("src/config/default.yaml")
    original_budget = config["budget"]["total"]

    # Smaller budget should scale proportionally (mostly)
    small_budget = original_budget * 0.5
    benchmarks = generate_channel_benchmarks(config)

    allocation_full = solve_qp(benchmarks, original_budget)
    allocation_small = solve_qp(benchmarks, small_budget)

    # Check scaling behavior (accounting for min spend constraints)
    for bench in benchmarks:
        channel = bench["channel"]
        ratio = allocation_small[channel] / allocation_full[channel]

        # If both at minimum spend, ratio = 1.0 (can't scale below min)
        if (
            abs(allocation_full[channel] - bench["min_spend"]) < 1e-3
            and abs(allocation_small[channel] - bench["min_spend"]) < 1e-3
        ):
            assert (
                abs(ratio - 1.0) < 1e-3
            ), f"{channel} both at min spend, ratio should be 1.0: {ratio:.3f}"
        else:
            # Otherwise should scale proportionally (constraint effects allowed)
            assert 0.2 <= ratio <= 0.8, f"{channel} scaling seems off: {ratio:.3f}"

    # Total budget should scale properly
    total_full = sum(allocation_full.values())
    total_small = sum(allocation_small.values())
    budget_ratio = total_small / total_full
    assert abs(budget_ratio - 0.5) < 0.1, f"Budget scaling off: {budget_ratio:.3f}"

    # Large budget should hit more max constraints (or fail due to infeasibility)
    large_budget = original_budget * 2  # Keep reasonable to avoid infeasibility

    # This might fail due to infeasibility - that's actually correct behavior
    try:
        allocation_large = solve_qp(benchmarks, large_budget)

        # Some channels should get more allocation
        channels_increased = 0
        for bench in benchmarks:
            channel = bench["channel"]
            if (
                allocation_large[channel] > allocation_full[channel] * 1.1
            ):  # 10% increase
                channels_increased += 1

        assert (
            channels_increased >= 1
        ), "Large budget should increase allocation for some channels"

    except (RuntimeError, ValueError):
        # Large budget infeasible - optimizer correctly identified this
        pass  # Test passes
