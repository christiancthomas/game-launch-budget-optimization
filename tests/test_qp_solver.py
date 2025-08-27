"""Test QP solver for budget optimization."""

import pytest
from src.opt.solve import solve_qp, validate_solution
from src.features.curves import quad_conversions


def create_test_benchmarks():
    """Create simple test data for solver testing."""
    return [
        {
            "channel": "google",
            "curve_a": 0.001,
            "curve_b": 1e-8,
            "min_spend": 5000,
            "max_spend": 30000,
        },
        {
            "channel": "meta",
            "curve_a": 0.0008,
            "curve_b": 8e-9,
            "min_spend": 3000,
            "max_spend": 25000,
        },
        {
            "channel": "tiktok",
            "curve_a": 0.0006,
            "curve_b": 6e-9,
            "min_spend": 2000,
            "max_spend": 20000,
        },
    ]


def test_solve_qp_basic():
    """Basic QP solving works with simple data."""
    benchmarks = create_test_benchmarks()
    total_budget = 50000

    allocation = solve_qp(benchmarks, total_budget)

    # Should return allocation for all channels
    assert len(allocation) == len(benchmarks)
    for ch in benchmarks:
        assert ch["channel"] in allocation
        assert allocation[ch["channel"]] > 0


def test_budget_conservation():
    """Solution spends exactly the total budget."""
    benchmarks = create_test_benchmarks()
    total_budget = 45000

    allocation = solve_qp(benchmarks, total_budget)

    # Budget should be fully allocated (within tolerance)
    total_allocated = sum(allocation.values())
    assert abs(total_allocated - total_budget) < 1e-6


def test_channel_bounds_respected():
    """Solution respects min/max spend per channel."""
    benchmarks = create_test_benchmarks()
    total_budget = 60000

    allocation = solve_qp(benchmarks, total_budget)

    # Check bounds for each channel
    for ch in benchmarks:
        spend = allocation[ch["channel"]]
        assert spend >= ch["min_spend"], f"{ch['channel']}: {spend} < {ch['min_spend']}"
        assert spend <= ch["max_spend"], f"{ch['channel']}: {spend} > {ch['max_spend']}"


def test_feasible_vs_infeasible():
    """Handle cases where constraints can't be satisfied."""
    benchmarks = create_test_benchmarks()

    # This should work (feasible)
    allocation = solve_qp(benchmarks, 50000)
    assert len(allocation) == len(benchmarks)

    # This should fail (budget too small for min spends)
    total_min = sum(ch["min_spend"] for ch in benchmarks)
    with pytest.raises(ValueError, match="Budget too small"):
        solve_qp(benchmarks, total_min - 1000)


def test_realistic_allocation():
    """Solution makes business sense with realistic data."""
    benchmarks = create_test_benchmarks()
    total_budget = 55000

    allocation = solve_qp(benchmarks, total_budget)

    # Channels with better curves should get more budget (generally)
    # Google has highest 'a' parameter so should get decent allocation
    google_spend = allocation["google"]
    assert google_spend > benchmarks[0]["min_spend"]

    # Total conversions should be positive and reasonable
    total_conversions = 0
    for ch in benchmarks:
        spend = allocation[ch["channel"]]
        conversions = quad_conversions(spend, ch["curve_a"], ch["curve_b"])
        total_conversions += conversions

    assert total_conversions > 0
    assert total_conversions < total_budget  # Sanity check


def test_validation_function():
    """Solution validation works correctly."""
    benchmarks = create_test_benchmarks()
    total_budget = 50000

    # Valid allocation
    valid_allocation = {"google": 20000, "meta": 18000, "tiktok": 12000}
    assert validate_solution(valid_allocation, benchmarks, total_budget)

    # Invalid: wrong budget total
    invalid_budget = {
        "google": 20000,
        "meta": 18000,
        "tiktok": 10000,  # Total = 48000, not 50000
    }
    assert not validate_solution(invalid_budget, benchmarks, total_budget)

    # Invalid: exceeds max spend
    invalid_bounds = {
        "google": 35000,  # Exceeds max_spend of 30000
        "meta": 10000,
        "tiktok": 5000,
    }
    assert not validate_solution(invalid_bounds, benchmarks, total_budget)


def test_edge_cases():
    """Handle edge cases gracefully."""
    benchmarks = create_test_benchmarks()

    # Empty benchmarks
    with pytest.raises(ValueError, match="Need at least one channel"):
        solve_qp([], 10000)

    # Zero/negative budget
    with pytest.raises(ValueError, match="Budget must be > 0"):
        solve_qp(benchmarks, 0)

    with pytest.raises(ValueError, match="Budget must be > 0"):
        solve_qp(benchmarks, -1000)
