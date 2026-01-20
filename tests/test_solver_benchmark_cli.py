import os
from pathlib import Path

import pytest

from absmt.sat_status import SatStatus
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
    benchmark.extra_info["peak_memory_mb"] = round(peak_memory_mb, 4)

    if actual_status == "timeout":
        benchmark.extra_info["status"] = "timeout"
    elif actual_status == "memout":
        benchmark.extra_info["status"] = "memout"
    elif actual_status != expected_status:
        if isinstance(expected_status, SatStatus):
            # 不一致の場合。テストを止めずに "wrong_answer" 等として記録
            benchmark.extra_info["status"] = "wrong_answer"
        else:
            # expected_status が None (不明) の場合は unknown として記録
            benchmark.extra_info["status"] = "unkown"
    else:
        # 一致した場合
        benchmark.extra_info["status"] = "success"
