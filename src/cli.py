"""CLI for budget optimization commands."""

import argparse
import sys
from pathlib import Path

from src.config.load import load_config
from src.data.synth import generate_channel_benchmarks, write_benchmarks_csv


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
