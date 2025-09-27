import pytest
import pandas as pd
import matplotlib.pyplot as plt
import tempfile
from pathlib import Path
from unittest.mock import patch

from src.viz.plots import (
    plot_allocation_breakdown,
    plot_simple_allocation_bar,
    create_full_dashboard,
)


@pytest.fixture
def sample_results_df():
    """Sample optimization results for testing."""
    return pd.DataFrame(
        [
            {
                "channel": "google",
                "optimal_spend": 25000,
                "predicted_conversions": 500,
                "cost_per_acquisition": 50,
            },
            {
                "channel": "meta",
                "optimal_spend": 30000,
                "predicted_conversions": 750,
                "cost_per_acquisition": 40,
            },
            {
                "channel": "tiktok",
                "optimal_spend": 20000,
                "predicted_conversions": 400,
                "cost_per_acquisition": 50,
            },
        ]
    )


@pytest.fixture
def sample_benchmarks_df():
    """Sample benchmarks data for testing."""
    return pd.DataFrame(
        [
            {
                "channel": "google",
                "curve_a": 0.02,
                "curve_b": 1e-7,
                "min_spend": 5000,
                "max_spend": 40000,
            },
            {
                "channel": "meta",
                "curve_a": 0.025,
                "curve_b": 8e-8,
                "min_spend": 3000,
                "max_spend": 35000,
            },
            {
                "channel": "tiktok",
                "curve_a": 0.02,
                "curve_b": 1e-7,
                "min_spend": 2000,
                "max_spend": 25000,
            },
        ]
    )


def test_simple_allocation_bar_basic(sample_results_df):
    """Test simple allocation bar chart runs without errors."""
    with patch("matplotlib.pyplot.show"):  # Don't actually show plot in tests
        plot_simple_allocation_bar(sample_results_df)

    # Close any open figures
    plt.close("all")


def test_allocation_breakdown_basic(sample_results_df):
    """Test allocation breakdown chart runs without errors."""
    with patch("matplotlib.pyplot.show"):
        plot_allocation_breakdown(sample_results_df)

    plt.close("all")


def test_simple_allocation_bar_with_save(sample_results_df):
    """Test that saving charts works correctly."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        temp_path = f.name

    try:
        with patch("matplotlib.pyplot.show"):
            plot_simple_allocation_bar(sample_results_df, save_path=temp_path)

        # Check file was created
        assert Path(temp_path).exists()
        assert Path(temp_path).stat().st_size > 0  # File has content

    finally:
        # Cleanup handling
        Path(temp_path).unlink(missing_ok=True)
        plt.close("all")


def test_create_full_dashboard_files(sample_benchmarks_df, sample_results_df):
    """Test that dashboard creates expected files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create CSV files for testing
        benchmarks_path = Path(temp_dir) / "benchmarks.csv"
        results_path = Path(temp_dir) / "results.csv"
        output_dir = Path(temp_dir) / "figures"

        sample_benchmarks_df.to_csv(benchmarks_path, index=False)
        sample_results_df.to_csv(results_path, index=False)

        # Run dashboard with show_plots=False to avoid display issues in tests
        with patch("matplotlib.pyplot.show"):
            create_full_dashboard(
                benchmarks_path=str(benchmarks_path),
                results_path=str(results_path),
                output_dir=str(output_dir),
                show_plots=False,
            )

        # Check expected files were created
        expected_files = [
            "allocation_breakdown.png",
            "channel_curves.png",
            "efficiency_analysis.png",
            "marginal_roi_comparison.png",
        ]

        for filename in expected_files:
            file_path = output_dir / filename
            assert file_path.exists(), f"Expected file {filename} not created"
            assert file_path.stat().st_size > 0, f"File {filename} is empty"

    plt.close("all")


def test_plot_functions_handle_empty_data():
    """Test that plot functions handle edge cases gracefully."""
    empty_df = pd.DataFrame(
        columns=[
            "channel",
            "optimal_spend",
            "predicted_conversions",
            "cost_per_acquisition",
        ]
    )

    with patch("matplotlib.pyplot.show"):
        try:
            # This might raise an error, which is acceptable behavior
            plot_simple_allocation_bar(empty_df)
        except (ValueError, IndexError):
            pass  # Expected for empty data

    plt.close("all")


def test_dataframe_requirements(sample_results_df):
    """Test that functions work with expected DataFrame structure."""
    # Verify our sample data has the expected columns
    required_columns = [
        "channel",
        "optimal_spend",
        "predicted_conversions",
        "cost_per_acquisition",
    ]

    for col in required_columns:
        assert col in sample_results_df.columns

    # Verify basic data types
    assert sample_results_df["optimal_spend"].dtype in ["float64", "int64"]
    assert sample_results_df["predicted_conversions"].dtype in ["float64", "int64"]
