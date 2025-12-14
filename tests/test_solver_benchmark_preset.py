from pathlib import Path

import pytest

from tests.benchmark_runner import run_in_subprocess  # 共通ロジックをインポート

REPO_ROOT = Path(__file__).resolve().parents[1]
PATHS_BASE_DIR = REPO_ROOT / "benchmarks" / "paths"


def get_benchmark_list_files(category: str) -> list[Path]:
    if not PATHS_BASE_DIR.exists():
        return []
    category_dir = PATHS_BASE_DIR / category
    if not category_dir.exists():
        return []
    return sorted(category_dir.glob("*.txt"))


def resolve_benchmark_paths(list_file_path: Path) -> list[Path]:
    if not list_file_path.exists():
        return []
    base_dir = list_file_path.parent
    paths = []
    with list_file_path.open("r", encoding="utf-8") as fh:
        for raw_line in fh:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            p = (base_dir / line).resolve()
            if p.exists():
                paths.append(p)
    return paths


def collect_benchmark_paths(category: str):
    all_paths = []
    for list_path in get_benchmark_list_files(category):
        benchmark_name = list_path.stem
        paths = resolve_benchmark_paths(list_path)
        all_paths.extend((category, benchmark_name, p) for p in paths)
    return all_paths


def _benchmark_id(val) -> str:
    category, benchmark_name, path = val
    return f"{category}/{benchmark_name}/{path.name}"


# --- テスト定義 ---


@pytest.mark.benchmark
@pytest.mark.parametrize(
    "benchmark_info", collect_benchmark_paths("QF_LIA"), ids=_benchmark_id
)
def test_qf_lia_solver_benchmark(benchmark, benchmark_info):
    category, benchmark_name, path = benchmark_info
    expected_status, actual_status, peak_memory = benchmark(
        run_in_subprocess, str(path)
    )

    benchmark.extra_info["peak_memory_mb"] = f"{peak_memory / (1024 * 1024):.2f} MB"
    benchmark.extra_info["category"] = category
    benchmark.extra_info["benchmark_set"] = benchmark_name
    assert actual_status == expected_status


@pytest.mark.benchmark(max_time=60)
@pytest.mark.parametrize(
    "benchmark_info", collect_benchmark_paths("LIA"), ids=_benchmark_id
)
def test_lia_solver_benchmark(benchmark, benchmark_info):
    category, benchmark_name, path = benchmark_info
    expected_status, actual_status, peak_memory = benchmark.pedantic(
        run_in_subprocess,
        args=(str(path),),
        rounds=1,
        iterations=1,
    )

    benchmark.extra_info["peak_memory_mb"] = f"{peak_memory / (1024 * 1024):.2f} MB"
    benchmark.extra_info["category"] = category
    benchmark.extra_info["benchmark_set"] = benchmark_name
    assert actual_status == expected_status
