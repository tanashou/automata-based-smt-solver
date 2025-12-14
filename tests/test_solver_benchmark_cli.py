from pathlib import Path

from tests.benchmark_runner import run_in_subprocess  # 共通ロジックをインポート


def test_solver_benchmark(benchmark, benchmark_file: Path, request):
    """Run solver for each .smt2 file in the directory specified by --benchmark-dir."""
    # タイムアウト値を取得
    timeout = request.config.getoption("--benchmark-timeout")

    # 実行
    expected_status, actual_status, peak_memory = benchmark(
        run_in_subprocess, str(benchmark_file), timeout
    )

    # メタデータの付与
    peak_memory_mb = peak_memory / (1024 * 1024)
    benchmark.extra_info["peak_memory_mb"] = f"{peak_memory_mb:.2f} MB"
    benchmark.extra_info["parent_dir"] = benchmark_file.parent.name
    benchmark.extra_info["filename"] = benchmark_file.name

    assert actual_status == expected_status
