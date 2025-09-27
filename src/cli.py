"""CLI for budget optimization commands."""

import argparse
import sys
from pathlib import Path
import pandas as pd

from src.config.load import load_config
from src.data.synth import generate_channel_benchmarks, write_benchmarks_csv
from src.opt.solve import solve_qp
from src.features.curves import quad_conversions
from src.viz.plots import create_full_dashboard, plot_simple_allocation_bar


def cmd_synth(args):
    """Generate synthetic channel benchmarks."""
    config = load_config(args.config)

    print("🎯 Generating synthetic channel benchmarks...")
    benchmarks = generate_channel_benchmarks(config)

    # Create output directory if needed
    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    write_benchmarks_csv(benchmarks, str(output_path))

    print(f"✅ Generated {len(benchmarks)} channel benchmarks")
    print(f"📄 Saved to: {output_path}")

    # Quick summary
    for bench in benchmarks:
        roi_at_max = bench["curve_a"] - 2 * bench["curve_b"] * bench["max_spend"]
        print(
            f"   {bench['channel']}: max_spend=${bench['max_spend']:.0f}, \
                ROI@max={roi_at_max:.4f}"
        )


def cmd_optimize(args):
    """Run budget optimization on channel benchmarks."""
    config = load_config(args.config)

    print("🚀 Running budget optimization...")

    # Load benchmarks from CSV
    benchmarks_path = Path(args.benchmarks)
    if not benchmarks_path.exists():
        raise FileNotFoundError(f"Benchmarks file not found: {benchmarks_path}")

    # Read CSV into list of dicts
    df = pd.read_csv(benchmarks_path)
    benchmarks = df.to_dict("records")

    # Get budget from config or args
    budget = args.budget or config.get("budget", {}).get("total", 1000)

    print(f"💰 Total budget: ${budget}")
    print(f"📊 Optimizing {len(benchmarks)} channels...")

    # Run optimization
    allocation = solve_qp(benchmarks, budget)

    print("\n✅ OPTIMIZATION COMPLETE!")
    print("=" * 60)
    print("OPTIMAL ALLOCATION:")
    print(f"{'Channel':15} | {'Spend':8} | {'Conversions':12} | {'CPA':8}")
    print("-" * 60)

    total_allocated = 0
    total_conversions = 0

    for ch in benchmarks:
        channel_name = ch["channel"]
        spend = allocation[channel_name]
        conversions = quad_conversions(spend, ch["curve_a"], ch["curve_b"])
        cpa = spend / conversions if conversions > 0 else float("inf")

        total_allocated += spend
        total_conversions += conversions

        print(
            f"{channel_name:15} | ${spend:7.0f} | "
            f"{conversions:7.0f} conv | ${cpa:5.0f} CPA"
        )

    print("-" * 60)
    total_cpa = (
        total_allocated / total_conversions if total_conversions > 0 else float("inf")
    )
    print(
        f"{'TOTAL':15} | ${total_allocated:7.0f} | "
        f"{total_conversions:7.0f} conv | "
        f"${total_cpa:5.0f} CPA"
    )
    print(f"\nBudget utilization: {total_allocated/budget*100:.1f}%")

    # Save results if requested
    if args.output:
        results_df = pd.DataFrame(
            [
                {
                    "channel": ch["channel"],
                    "optimal_spend": allocation[ch["channel"]],
                    "predicted_conversions": quad_conversions(
                        allocation[ch["channel"]], ch["curve_a"], ch["curve_b"]
                    ),
                    "cost_per_acquisition": (
                        allocation[ch["channel"]]
                        / quad_conversions(
                            allocation[ch["channel"]], ch["curve_a"], ch["curve_b"]
                        )
                        if quad_conversions(
                            allocation[ch["channel"]], ch["curve_a"], ch["curve_b"]
                        )
                        > 0
                        else float("inf")
                    ),
                }
                for ch in benchmarks
            ]
        )

        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        results_df.to_csv(output_path, index=False)
        print(f"📄 Results saved to: {output_path}")


def cmd_visualize(args):
    """Generate visualizations for optimization results."""
    print("Generating optimization visualizations...")

    # Check if required files exist
    benchmarks_path = Path(args.benchmarks)
    results_path = Path(args.results)

    if not benchmarks_path.exists():
        raise FileNotFoundError(f"Benchmarks file not found: {benchmarks_path}")

    if not results_path.exists():
        raise FileNotFoundError(f"Results file not found: {results_path}")

    # Generate visualizations
    if args.dashboard:
        create_full_dashboard(
            benchmarks_path=str(benchmarks_path),
            results_path=str(results_path),
            output_dir=args.output_dir,
            show_plots=not args.no_show,
        )
    else:
        # Simple allocation chart only
        import pandas as pd

        results_df = pd.read_csv(results_path)

        output_path = None
        if args.output_dir:
            output_dir = Path(args.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / "allocation_chart.png"

        plot_simple_allocation_bar(results_df, save_path=output_path)

        if not args.no_show:
            print("✅ Chart displayed successfully!")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Budget optimization tools")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Synth command
    synth_parser = subparsers.add_parser("synth", help="Generate synthetic data")
    synth_parser.add_argument(
        "--config", default="src/config/default.yaml", help="Path to config file"
    )
    synth_parser.add_argument(
        "--out", default="data/raw/channel_benchmarks.csv", help="Output CSV path"
    )
    synth_parser.set_defaults(func=cmd_synth)

    # Optimize command
    optimize_parser = subparsers.add_parser("optimize", help="Run budget optimization")
    optimize_parser.add_argument(
        "--config", default="src/config/default.yaml", help="Path to config file"
    )
    optimize_parser.add_argument(
        "--benchmarks",
        default="data/raw/channel_benchmarks.csv",
        help="Path to channel benchmarks CSV",
    )
    optimize_parser.add_argument(
        "--budget", type=float, help="Total budget to optimize (overrides config)"
    )
    optimize_parser.add_argument(
        "--output", help="Path to save optimization results CSV"
    )
    optimize_parser.set_defaults(func=cmd_optimize)

    # Visualize command
    viz_parser = subparsers.add_parser("visualize", help="Generate visualizations")
    viz_parser.add_argument(
        "--benchmarks",
        default="data/raw/channel_benchmarks.csv",
        help="Path to channel benchmarks CSV",
    )
    viz_parser.add_argument(
        "--results",
        default="data/processed/optimization_results.csv",
        help="Path to optimization results CSV",
    )
    viz_parser.add_argument(
        "--output-dir",
        default="experiments/results/figures",
        help="Directory to save charts",
    )
    viz_parser.add_argument(
        "--dashboard", action="store_true", help="Generate full dashboard (all charts)"
    )
    viz_parser.add_argument(
        "--no-show", action="store_true", help="Don't display charts, just save them"
    )
    viz_parser.set_defaults(func=cmd_visualize)

    # Parse and execute
    args = parser.parse_args()

    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)

    try:
        args.func(args)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
