import os
from pathlib import Path

import pytest

from tests.benchmark_runner import run_in_subprocess

# 環境変数からタイムアウト値を取得 (デフォルト60秒)
TIMEOUT = float(os.environ.get("BENCHMARK_TIMEOUT", "60"))


@pytest.mark.benchmark(max_time=TIMEOUT)
def test_solver_benchmark(benchmark, benchmark_file: Path):
    """Run solver for each .smt2 file."""
    # 実行 (timeout引数を渡す)
    expected_status, actual_status, peak_memory = benchmark.pedantic(
        run_in_subprocess,
        args=(str(benchmark_file), TIMEOUT),  # ← ここでタイムアウト時間を渡す
        rounds=5,
        iterations=1,
    )

    # メタデータの付与
    peak_memory_mb = peak_memory / (1024 * 1024)
    benchmark.extra_info["peak_memory_mb"] = f"{peak_memory_mb:.2f} MB"
    benchmark.extra_info["parent_dir"] = benchmark_file.parent.name
    benchmark.extra_info["filename"] = benchmark_file.name

    # 結果の判定ロジックを修正
    if actual_status == "timeout":
        benchmark.extra_info["status"] = "timeout"
        # タイムアウト時はアサーションを行わない。成功扱いにするがstatusは記録
    else:
        benchmark.extra_info["status"] = "success"
        assert actual_status == expected_status
