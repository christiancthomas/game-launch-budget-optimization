"""Test synthetic data generation meets contract requirements."""

import tempfile
import csv
from pathlib import Path

from src.config.load import load_config
from src.data.synth import (
    generate_channel_benchmarks,
    write_benchmarks_csv,
    derive_quad_params,
    sample_base_metrics,
)


def test_generate_benchmarks_basic():
    """Basic benchmarks generation works."""
    config = load_config("src/config/default.yaml")

    benchmarks = generate_channel_benchmarks(config)

    # Should have one benchmark per channel
    assert len(benchmarks) == len(config["channels"])

    # Check structure
    required_fields = [
        "channel",
        "cpc",
        "ctr",
        "cvr",
        "min_spend",
        "max_spend",
        "curve_a",
        "curve_b",
    ]
    for bench in benchmarks:
        for field in required_fields:
            assert field in bench


def test_deterministic_with_seed():
    """Same seed produces same results."""
    config = load_config("src/config/default.yaml")

    benchmarks1 = generate_channel_benchmarks(config)
    benchmarks2 = generate_channel_benchmarks(config)

    # Should be identical (same seed)
    assert benchmarks1 == benchmarks2


def test_quadratic_params_make_sense():
    """Quadratic parameters are mathematically sound."""
    config = load_config("src/config/default.yaml")
    benchmarks = generate_channel_benchmarks(config)

    for bench in benchmarks:
        a, b = bench["curve_a"], bench["curve_b"]
        max_spend = bench["max_spend"]

        # Both coefficients should be positive
        assert a > 0, f"{bench['channel']}: a must be > 0"
        assert b > 0, f"{bench['channel']}: b must be > 0"

        # ROI at max spend should be positive but small
        roi_at_max = a - 2 * b * max_spend
        assert roi_at_max > 0, f"{bench['channel']}: ROI at max spend must be positive"
        assert roi_at_max < a, f"{bench['channel']}: ROI should decrease with spend"


def test_metric_ranges_reasonable():
    """Generated metrics fall within reasonable ranges."""
    config = load_config("src/config/default.yaml")
    benchmarks = generate_channel_benchmarks(config)

    for bench in benchmarks:
        # Should be within or close to config ranges (allowing for channel multipliers)
        assert 0.1 <= bench["cpc"] <= 10.0, f"CPC out of range: {bench['cpc']}"
        assert 0.001 <= bench["ctr"] <= 0.20, f"CTR out of range: {bench['ctr']}"
        assert 0.001 <= bench["cvr"] <= 0.20, f"CVR out of range: {bench['cvr']}"


def test_csv_output_works():
    """CSV output has correct structure."""
    config = load_config("src/config/default.yaml")
    benchmarks = generate_channel_benchmarks(config)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        write_benchmarks_csv(benchmarks, f.name)

        # Read it back and verify
        with open(f.name, "r") as rf:
            reader = csv.DictReader(rf)
            rows = list(reader)

            assert len(rows) == len(benchmarks)
            assert rows[0].keys() == benchmarks[0].keys()

        Path(f.name).unlink()


def test_base_metrics_sampling():
    """Base metrics sampling works correctly."""
    config = load_config("src/config/default.yaml")

    metrics = sample_base_metrics(config)

    # Should have right structure
    assert set(metrics.keys()) == {"cpc", "ctr", "cvr"}

    # Should be within config ranges
    ranges = config["synth_data"]
    assert ranges["cpc_range"][0] <= metrics["cpc"] <= ranges["cpc_range"][1]
    assert ranges["ctr_range"][0] <= metrics["ctr"] <= ranges["ctr_range"][1]
    assert ranges["cvr_range"][0] <= metrics["cvr"] <= ranges["cvr_range"][1]


def test_quad_params_derivation():
    """Quadratic parameter derivation is mathematically correct."""
    cpc, ctr, cvr, max_spend = 2.0, 0.03, 0.04, 10000

    a, b = derive_quad_params(cpc, ctr, cvr, max_spend)

    # a should equal funnel efficiency
    expected_a = (ctr * cvr) / cpc
    assert abs(a - expected_a) < 1e-10

    # At max spend, efficiency should drop by target percentage (30%)
    efficiency_at_max = a - b * max_spend
    efficiency_drop = 1 - (efficiency_at_max / a)
    assert abs(efficiency_drop - 0.3) < 1e-10  # Should be 30%
