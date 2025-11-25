# ruff: noqa: T201
"""Analyze benchmark tournament structure results from CSV file.

This script reads tournament structure benchmark results and displays
the fastest and slowest tournament structure patterns for intersect_all operations.
"""

import csv
import json
import sys
from pathlib import Path

# Threshold for displaying memory in KB instead of MB
MEMORY_KB_THRESHOLD_MB = 0.01  # 0.01 MB = 10 KB


def format_memory(memory_mb: float) -> str:
    """Format memory value with appropriate unit (KB or MB).

    Peak memory values from tracemalloc are always non-negative.
    Values below 10 KB (0.01 MB) are displayed in KB for readability.

    Args:
        memory_mb: Memory value in MB (from tracemalloc peak measurement)

    Returns:
        Formatted string with appropriate unit

    """
    # Very small values: display in KB for better readability
    if memory_mb < MEMORY_KB_THRESHOLD_MB:
        memory_kb = memory_mb * 1024
        return f"{memory_kb:.2f} KB"
    # Regular values: display in MB
    return f"{memory_mb:.2f} MB"


def list_available_benchmarks() -> list[str]:
    """List all available benchmark IDs."""
    results_dir = Path(__file__).parent.parent / ".benchmarks" / "tournament_structures"
    if not results_dir.exists():
        return []

    # Find all CSV files
    csv_files = results_dir.glob("*.csv")
    return sorted([f.stem for f in csv_files])


def get_benchmark_metadata(benchmark_id: str) -> dict | None:
    """Get metadata for a specific benchmark.

    Args:
        benchmark_id: The benchmark identifier

    Returns:
        Metadata dictionary or None if not found

    """
    metadata_file = (
        Path(__file__).parent.parent
        / ".benchmarks"
        / "tournament_structures"
        / f"{benchmark_id}_meta.json"
    )
    if not metadata_file.exists():
        return None

    with metadata_file.open() as f:
        return json.load(f)


def analyze_results(  # noqa: C901, PLR0912, PLR0915
    csv_path: str | None = None, benchmark_id: str | None = None
) -> None:
    """Analyze benchmark results and display statistics.

    Args:
        csv_path: Path to the CSV file containing benchmark results
        benchmark_id: Benchmark ID to analyze (alternative to csv_path)

    """
    # Determine CSV file path
    if benchmark_id:
        csv_file = (
            Path(__file__).parent.parent
            / ".benchmarks"
            / "tournament_structures"
            / f"{benchmark_id}.csv"
        )
        if not csv_file.exists():
            print(f"Error: Benchmark '{benchmark_id}' not found.")
            print("\nAvailable benchmarks:")
            for bid in list_available_benchmarks():
                print(f"  - {bid}")
            sys.exit(1)
    elif csv_path:
        csv_file = Path(csv_path)
        if not csv_file.exists():
            print(f"Error: File '{csv_path}' not found.")
            print("Run the benchmark test first:")
            print(
                "  pytest tests/test_intersect_all_permutation_benchmark.py::"
                "test_single_intersect_all_benchmark_all_structures --benchmark-only"
            )
            sys.exit(1)
        # Extract benchmark_id from filename
        benchmark_id = csv_file.stem
    else:
        # No arguments provided, list available benchmarks
        available = list_available_benchmarks()
        if not available:
            print("No benchmark results found in .benchmarks/tournament_structures/")
            print("Run the benchmark test first:")
            print(
                "  pytest tests/test_intersect_all_permutation_benchmark.py::"
                "test_single_intersect_all_benchmark_all_structures --benchmark-only"
            )
            sys.exit(1)

        print("Available benchmarks:")
        for bid in available:
            print(f"  - {bid}")
        print(f"\nAnalyzing latest: {available[-1]}")
        csv_file = (
            Path(__file__).parent.parent
            / ".benchmarks"
            / "tournament_structures"
            / f"{available[-1]}.csv"
        )
        benchmark_id = available[-1]

    # Read CSV data
    with csv_file.open() as f:
        reader = csv.DictReader(f)
        data = list(reader)

    if not data:
        print("Error: CSV file is empty.")
        sys.exit(1)

    # Sort by time
    sorted_by_time = sorted(data, key=lambda x: float(x["time_sec"]))

    # Display results
    print("=" * 80)
    print("BENCHMARK RESULTS ANALYSIS")
    print("=" * 80)
    print(f"\nBenchmark ID: {benchmark_id}")

    # Display metadata if available
    metadata = get_benchmark_metadata(benchmark_id)
    if metadata:
        print(f"Number of automata: {metadata.get('num_automata', 'N/A')}")
        if metadata.get("file_path"):
            print(f"Source file: {metadata['file_path']}")

    print(f"\nTotal tournament structures tested: {len(data)}")
    print()

    # Top 10 fastest
    print("=" * 80)
    print("TOP 10 FASTEST TOURNAMENT STRUCTURES")
    print("=" * 80)
    print(f"{'Rank':<6} {'Structure Pattern':<30} {'Time (sec)':<15} {'Memory'}")
    print("-" * 80)
    for i, row in enumerate(sorted_by_time[:10], 1):
        structure = row["structure"]
        time_sec = float(row["time_sec"])
        memory_mb = float(row["memory_mb"])
        memory_str = format_memory(memory_mb)
        print(f"{i:<6} {structure:<30} {time_sec:<15.6f} {memory_str}")

    print()

    # Top 10 slowest
    print("=" * 80)
    print("TOP 10 SLOWEST TOURNAMENT STRUCTURES")
    print("=" * 80)
    print(f"{'Rank':<6} {'Structure Pattern':<30} {'Time (sec)':<15} {'Memory'}")
    print("-" * 80)
    for i, row in enumerate(sorted_by_time[-10:], 1):
        structure = row["structure"]
        time_sec = float(row["time_sec"])
        memory_mb = float(row["memory_mb"])
        memory_str = format_memory(memory_mb)
        print(f"{i:<6} {structure:<30} {time_sec:<15.6f} {memory_str}")

    print()

    # Statistics
    fastest = sorted_by_time[0]
    slowest = sorted_by_time[-1]
    fastest_time = float(fastest["time_sec"])
    slowest_time = float(slowest["time_sec"])

    all_times = [float(row["time_sec"]) for row in data]
    all_memories = [float(row["memory_mb"]) for row in data]
    avg_time = sum(all_times) / len(all_times)
    avg_memory = sum(all_memories) / len(all_memories)

    print("=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    print(f"Fastest structure:     {fastest['structure']}")
    print(f"  Time:                {fastest_time:.6f} sec")
    print(f"  Memory:              {format_memory(float(fastest['memory_mb']))}")
    print()
    print(f"Slowest structure:     {slowest['structure']}")
    print(f"  Time:                {slowest_time:.6f} sec")
    print(f"  Memory:              {format_memory(float(slowest['memory_mb']))}")
    print()
    print(f"Time difference:       {slowest_time - fastest_time:.6f} sec")
    print(f"Slowdown factor:       {slowest_time / fastest_time:.2f}x")
    print(f"Percentage slower:     {(slowest_time / fastest_time - 1) * 100:.1f}%")
    print()
    print(f"Average time:          {avg_time:.6f} sec")
    print(f"Average memory:        {format_memory(avg_memory)}")
    print()

    # Sort by memory
    sorted_by_memory = sorted(data, key=lambda x: float(x["memory_mb"]))
    lowest_mem = sorted_by_memory[0]
    highest_mem = sorted_by_memory[-1]

    print("=" * 80)
    print("MEMORY USAGE")
    print("=" * 80)
    print(f"Lowest memory structure:  {lowest_mem['structure']}")
    print(f"  Memory:                 {format_memory(float(lowest_mem['memory_mb']))}")
    print(f"  Time:                   {float(lowest_mem['time_sec']):.6f} sec")
    print()
    print(f"Highest memory structure: {highest_mem['structure']}")
    print(f"  Memory:                 {format_memory(float(highest_mem['memory_mb']))}")
    print(f"  Time:                   {float(highest_mem['time_sec']):.6f} sec")
    print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze benchmark tournament structure results"
    )
    parser.add_argument(
        "benchmark_id",
        nargs="?",
        help="Benchmark ID to analyze (e.g., 'inline_abc123')",
    )
    parser.add_argument(
        "--csv",
        dest="csv_file",
        help="Direct path to CSV file (alternative to benchmark_id)",
    )
    args = parser.parse_args()

    analyze_results(csv_path=args.csv_file, benchmark_id=args.benchmark_id)
