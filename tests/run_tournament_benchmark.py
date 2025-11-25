# ruff: noqa: T201
"""Run tournament structure benchmark for a specific SMT2 file.

Usage:
    python run_tournament_benchmark.py path/to/file.smt2
    python run_tournament_benchmark.py path/to/file.smt2 --name custom_name
"""

import argparse
import logging
import sys
from pathlib import Path

# Add tests directory to path to import benchmark functions
sys.path.insert(0, str(Path(__file__).parent / "tests"))

from test_intersect_all_permutation_benchmark import run_benchmark_for_file


def main() -> None:
    """Run the benchmark runner."""
    # Configure logging to show progress
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )

    parser = argparse.ArgumentParser(
        description="Run tournament structure benchmark for an SMT2 file"
    )
    parser.add_argument("smt2_file", help="Path to the SMT2 file to benchmark")
    parser.add_argument(
        "--name",
        help="Custom name for the benchmark (default: derived from filename)",
    )

    args = parser.parse_args()

    # Check if file exists
    smt2_path = Path(args.smt2_file)
    if not smt2_path.exists():
        print(f"Error: File not found: {args.smt2_file}")
        sys.exit(1)

    print(f"Running tournament structure benchmark for: {args.smt2_file}")
    print("-" * 80)

    try:
        run_benchmark_for_file(str(smt2_path), args.name)
        print("\n" + "=" * 80)
        print("Benchmark completed successfully!")
        print("=" * 80)
        print("\nTo analyze the results, run:")
        benchmark_id = args.name or smt2_path.stem
        print(f"  python scripts/analyze_benchmark_results.py {benchmark_id}")
    except Exception as e:  # noqa: BLE001
        print(f"\nError running benchmark: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
