"""Tests the quadratic curve math functions from curves.py."""

from src.features.curves import (
    quad_conversions,
    quad_grad,
    validate_curve_params,
    conversions_at_spend_levels,
)


def test_quad_conversions_basic():
    """Tests that the basic quadratic conversion calculation works."""
    a, b = 0.001, 1e-8
    spend = 10000

    result = quad_conversions(spend, a, b)

    # Should be positive and reasonable
    assert result > 0
    # Should equal a*spend - b*spend^2
    expected = a * spend - b * spend**2
    assert abs(result - expected) < 1e-10  # Floating point tolerance


def test_quad_grad_decreasing():
    """Tests that marginal ROI decreases with higher spend."""
    a, b = 0.001, 1e-8
    spend1, spend2 = 5000, 10000

    roi1 = quad_grad(spend1, a, b)
    roi2 = quad_grad(spend2, a, b)

    # ROI should decrease as spend increases
    assert roi1 > roi2
    assert roi1 > 0
    assert roi2 > 0


def test_curve_properties():
    """Tests that the curve has correct mathematical properties (concave, monotone)."""
    a, b = 0.001, 1e-8
    spend_levels = [1000, 5000, 10000, 15000]

    conversions = [quad_conversions(s, a, b) for s in spend_levels]
    rois = [quad_grad(s, a, b) for s in spend_levels]

    # Conversions should be monotone increasing
    for i in range(1, len(conversions)):
        assert conversions[i] > conversions[i - 1]

    # ROI should be monotone decreasing
    for i in range(1, len(rois)):
        assert rois[i] < rois[i - 1]

    # All ROI should be positive in reasonable range
    assert all(roi > 0 for roi in rois)


def test_realistic_parameters():
    """Curves should work with realistic marketing parameters."""
    # Use parameters similar to what synth.py generates
    a = 0.0008  # Reasonable efficiency
    b = 1e-8  # Small curvature
    max_spend = 25000

    # Should have positive ROI at max spend
    roi_at_max = quad_grad(max_spend, a, b)
    assert roi_at_max > 0

    # Total conversions should be reasonable
    total_conversions = quad_conversions(max_spend, a, b)
    assert total_conversions > 0
    assert total_conversions < max_spend  # Sanity check


def test_validate_curve_params():
    """Parameter validation works correctly."""
    # Valid params
    assert validate_curve_params(0.001, 1e-8) is True

    # Invalid params
    assert validate_curve_params(-0.001, 1e-8) is False  # Negative a
    assert validate_curve_params(0.001, -1e-8) is False  # Negative b
    assert validate_curve_params(0, 1e-8) is False  # Zero a
    assert validate_curve_params(0.001, 0) is False  # Zero b


def test_batch_conversions():
    """Batch conversion calculation works."""
    a, b = 0.001, 1e-8
    spend_levels = [1000, 5000, 10000]

    results = conversions_at_spend_levels(spend_levels, a, b)

    assert len(results) == len(spend_levels)
    assert all(r > 0 for r in results)

    # Should match individual calculations
    for spend, result in zip(spend_levels, results):
        expected = quad_conversions(spend, a, b)
        assert abs(result - expected) < 1e-10


def test_batch_conversions_invalid_params():
    """Batch conversion fails with invalid parameters."""
    spend_levels = [1000, 5000]

    try:
        conversions_at_spend_levels(spend_levels, -0.001, 1e-8)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass  # Expected
