"""CLI for budget optimization commands."""

import argparse
import sys
from pathlib import Path
import pandas as pd

from src.config.load import load_config
from src.data.synth import generate_channel_benchmarks, write_benchmarks_csv
from src.opt.solve import solve_qp
from src.features.curves import quad_conversions


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
    print(f"{'Channel':15} | {'Spend':8} | {'Conversions':12} | {'Eff (conv/$)':12}")
    print("-" * 60)

    total_allocated = 0
    total_conversions = 0

    for ch in benchmarks:
        channel_name = ch["channel"]
        spend = allocation[channel_name]
        conversions = quad_conversions(spend, ch["curve_a"], ch["curve_b"])
        efficiency = conversions / spend if spend > 0 else 0

        total_allocated += spend
        total_conversions += conversions

        print(
            f"{channel_name:15} | ${spend:7.0f} | "
            f"{conversions:7.0f} conv | {efficiency:4.1f} conv/$"
        )

    print("-" * 60)
    print(
        f"{'TOTAL':15} | ${total_allocated:7.0f} | "
        f"{total_conversions:7.0f} conv | "
        f"{total_conversions/total_allocated:4.1f} conv/$"
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
                    "efficiency_conv_per_dollar": quad_conversions(
                        allocation[ch["channel"]], ch["curve_a"], ch["curve_b"]
                    )
                    / allocation[ch["channel"]],
                }
                for ch in benchmarks
            ]
        )

        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        results_df.to_csv(output_path, index=False)
        print(f"📄 Results saved to: {output_path}")


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
