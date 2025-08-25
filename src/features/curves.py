"""
Mathematical functions for modeling marketing spend curves.

Implements quadratic saturation curves to capture diminishing returns
in digital advertising performance.
"""


def quad_conversions(spend: float, a: float, b: float) -> float:
    """
    Conversions as a quadratic function of spend.

    Business logic:
        This models the diminishing returns / saturation concept: after a certain point,
        each additional dollar spent yields progressively fewer conversions.

    Math:
        `y = a * spend - b * spend^2`
        Where:
        - 'y' is the total conversions at a level of spend
        - 'a' is the initial conversions per dollar (≈ CVR * CTR / CPC)
        - 'b' is the curvature that flattens performance as spend grows

    This is intentionally simple for V1: concave, monotone-increasing in our operating
    range, and easy to optimize with quadratic programming. Very likely that we'll build
    upon this in future versions with more advanced logic.
    """
    return (a * spend) - (b * spend**2)


def quad_grad(spend: float, a: float, b: float) -> float:
    """
    Marginal ROI (gradient) at a given spend level.

    Business logic:
        Shows the incremental conversions per additional dollar spent.
        Decreases as spend increases (diminishing returns).

    Math:
        `dy/dx = a - 2 * b * spend`
        First derivative of the quadratic curve.
    """
    return a - (2 * b * spend)


def validate_curve_params(a, b):
    """Check if curve params make business sense."""
    # Need positive coefficients for realistic diminishing returns
    return a > 0 and b > 0


def conversions_at_spend_levels(spend_levels: list, a: float, b: float) -> list[float]:
    """Batch calculate conversions for multiple spend levels."""
    if not validate_curve_params(a, b):
        raise ValueError("Invalid curve parameters")

    # Useful for plotting and analysis later
    return [quad_conversions(spend, a, b) for spend in spend_levels]
