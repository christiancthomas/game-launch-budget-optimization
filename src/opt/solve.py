"""Quadratic programming solver for budget allocation."""

import numpy as np
from scipy.optimize import minimize
from src.features.curves import quad_conversions


class OptimizationHistoryTracker:
    """Captures solver progress for convergence visualization."""

    def __init__(self, benchmarks: list[dict], total_budget: float):
        self.benchmarks = benchmarks
        self.total_budget = total_budget
        self.channel_names = [ch["channel"] for ch in benchmarks]

        # Storage for iteration history
        self.iterations = []
        self.objectives = []
        self.budget_errors = []
        self.spend_history = {f"spend_{ch}": [] for ch in self.channel_names}

        self.iteration_count = 0

    def __call__(self, xk):
        """Called by scipy after each iteration with current solution."""
        self.iteration_count += 1
        self.iterations.append(self.iteration_count)

        # Calculate objective (total conversions)
        total_conversions = sum(
            quad_conversions(spend, ch["curve_a"], ch["curve_b"])
            for spend, ch in zip(xk, self.benchmarks)
        )
        self.objectives.append(total_conversions)

        # Calculate budget constraint error
        budget_error = self.total_budget - np.sum(xk)
        self.budget_errors.append(budget_error)

        # Store per-channel spends
        for ch_name, spend in zip(self.channel_names, xk):
            self.spend_history[f"spend_{ch_name}"].append(spend)

    def get_history(self) -> dict:
        """Return collected history as dict for visualization."""
        return {
            "iteration": self.iterations,
            "objective": self.objectives,
            "budget_error": self.budget_errors,
            **self.spend_history,
        }


def solve_qp(benchmarks: list[dict], total_budget: float, track_history: bool = False):
    """
    Allocate budget across channels to maximize conversions.

    Business logic:
        Takes channel performance curves and budget constraint,
        finds optimal spend allocation that maximizes total conversions
        while respecting min/max spend limits per channel.

    Math:
        Quadratic programming problem:
        We want to maximize: sum(aᵢ * spendᵢ - bᵢ * spendᵢ²)
        while subject to: sum(spendᵢ) = budget, min_spendᵢ ≤ spendᵢ ≤ max_spendᵢ
        where aᵢ, bᵢ are curve parameters for channel i.

    Uses SLSQP (Sequential Least Squares Programming) for efficiency.

    Set track_history=True to get iteration data back for convergence viz.
    """
    if not benchmarks:
        raise ValueError("Need at least one channel to optimize")

    if total_budget <= 0:
        raise ValueError("Budget must be > 0")

    # Check if problem is feasible based on available spend
    total_min_spend = sum(ch["min_spend"] for ch in benchmarks)
    if total_min_spend > total_budget:
        raise ValueError(
            f"Budget too small for min spends ({total_min_spend} > {total_budget})"
        )

    # Build scipy optimization problem
    objective_fn = build_objective_function(benchmarks)
    constraints, bounds = build_constraints(benchmarks, total_budget)

    # Initial guess: distribute budget proportionally to max_spend
    total_max = sum(ch["max_spend"] for ch in benchmarks)
    x0 = np.array([total_budget * ch["max_spend"] / total_max for ch in benchmarks])

    # Set up history tracking if requested
    tracker = (
        OptimizationHistoryTracker(benchmarks, total_budget) if track_history else None
    )

    # Solve the QP problem
    result = minimize(
        objective_fn,
        x0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        callback=tracker,
        options={"ftol": 1e-9, "disp": False},
    )

    if not result.success:
        raise RuntimeError(f"Optimization failed: {result.message}")

    # Package results
    allocation = {
        ch["channel"]: float(spend) for ch, spend in zip(benchmarks, result.x)
    }

    # Validate solution
    if not validate_solution(allocation, benchmarks, total_budget):
        raise RuntimeError("Solution doesn't meet constraints")

    if track_history:
        return allocation, tracker.get_history()

    return allocation


def build_objective_function(benchmarks: list[dict]):
    """Build the objective function for scipy.minimize. This is the core
    mathematical heart of the optimization sequence.

    Returns: a closure function that calculates the total conversions
    for any spend allocation."""

    def objective(x):
        # Scipy minimizes, so we negate to maximize conversions
        total_conversions = 0
        for i, ch in enumerate(benchmarks):
            spend = x[i]
            conversions = quad_conversions(spend, ch["curve_a"], ch["curve_b"])
            total_conversions += conversions
        return (
            -total_conversions
        )  # Negate for maximization (scipy minimizes by default)

    return objective


def build_constraints(benchmarks: list[dict], total_budget: float):
    """Builds constraint functions and bounds for the optimizer."""

    # Budget equality constraint: sum(spends) = total_budget
    def budget_constraint(x):
        return total_budget - np.sum(x)  # Should equal 0

    constraint = {"type": "eq", "fun": budget_constraint}

    # Channel bounds: min_spend <= spend <= max_spend
    bounds = [(ch["min_spend"], ch["max_spend"]) for ch in benchmarks]

    return [constraint], bounds


def validate_solution(allocation: dict, benchmarks: list[dict], total_budget: float):
    """Verify solution meets all constraints."""
    tolerance = 1e-6  # Numerical tolerance for floating point comparisons

    # Check budget constraint
    total_allocated = sum(allocation.values())
    if abs(total_allocated - total_budget) > tolerance:
        return False

    # Check channel bounds
    for ch in benchmarks:
        spend = allocation[ch["channel"]]
        if spend < ch["min_spend"] - tolerance or spend > ch["max_spend"] + tolerance:
            return False

    return True
