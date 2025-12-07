import time
from multiprocessing import Process, Queue
from pathlib import Path
from typing import TypeVar

import psutil
import pytest
from typing_extensions import ParamSpec

from absmt.solver import Solver

P = ParamSpec("P")
R = TypeVar("R")

MAX_MEMORY_BYTES = 4 * 1024 * 1024 * 1024  # 4 GB
TIMEOUT_SECONDS = 60

REPO_ROOT = Path(__file__).resolve().parents[1]
PATHS_BASE_DIR = REPO_ROOT / "benchmarks" / "paths"


def get_benchmark_list_files(category: str) -> list[Path]:
    """Get all .txt files from a specific category directory.

    Args:
        category: Either "LIA" or "QF_LIA"

    Returns:
        List of .txt files in the category directory

    """
    if not PATHS_BASE_DIR.exists():
        return []

    category_dir = PATHS_BASE_DIR / category
    if not category_dir.exists():
        return []

    return sorted(category_dir.glob("*.txt"))


def resolve_benchmark_paths(list_file_path: Path) -> list[Path]:
    """Resolve .smt2 file paths from a benchmark list file.

    Returns an empty list if the list file doesn't exist or has no valid entries.
    """
    if not list_file_path.exists():
        return []

    base_dir = list_file_path.parent
    paths: list[Path] = []

    with list_file_path.open("r", encoding="utf-8") as fh:
        for raw_line in fh:
            line = raw_line.strip()
            # ignore empty lines and comments
            if not line or line.startswith("#"):
                continue

            p = (base_dir / line).resolve()
            if p.exists():
                paths.append(p)

    return paths


def collect_benchmark_paths(category: str) -> list[tuple[str, str, Path]]:
    """Collect benchmark paths from a specific category.

    Args:
        category: Either "LIA" or "QF_LIA"

    Returns:
        List of tuples: (category, benchmark_set_name, path_to_smt2_file)

    """
    all_paths: list[tuple[str, str, Path]] = []
    benchmark_list_files = get_benchmark_list_files(category)

    for list_path in benchmark_list_files:
        benchmark_name = list_path.stem  # e.g., "prime-cone"
        paths = resolve_benchmark_paths(list_path)
        all_paths.extend((category, benchmark_name, p) for p in paths)

    if not all_paths:
        pytest.skip(
            f"No benchmark files found for {category}",
            allow_module_level=True,
        )

    return all_paths


def collect_qf_lia_benchmark_paths() -> list[tuple[str, str, Path]]:
    """Collect QF_LIA benchmark paths.

    Returns:
        List of tuples: (category, benchmark_set_name, path_to_smt2_file)

    """
    return collect_benchmark_paths("QF_LIA")


def collect_lia_benchmark_paths() -> list[tuple[str, str, Path]]:
    """Collect LIA benchmark paths.

    Returns:
        List of tuples: (category, benchmark_set_name, path_to_smt2_file)

    """
    return collect_benchmark_paths("LIA")


def solver_worker(path_str: str, result_queue: Queue):
    try:
        solver = Solver()
        expected_status = solver.read_from_smtlib(path_str, is_file_path=True)
        actual_status = solver.solve()
        result_queue.put(("ok", (expected_status, actual_status)))
    except Exception as e:  # noqa: BLE001
        result_queue.put(("error", e))


def run_in_subprocess(path_str: str):
    result_queue = Queue()
    p = Process(target=solver_worker, args=(path_str, result_queue))
    p.start()

    process = psutil.Process(p.pid)
    start_time = time.time()

    peak_memory_bytes = 0

    while p.is_alive():
        if time.time() - start_time > TIMEOUT_SECONDS:
            p.terminate()
            p.join()
            pytest.fail(f"Timeout ({TIMEOUT_SECONDS}s) exceeded for {path_str}")

        try:
            mem_info = process.memory_info().rss
            peak_memory_bytes = max(peak_memory_bytes, mem_info)
            if mem_info > MAX_MEMORY_BYTES:
                p.terminate()
                p.join()
                pytest.skip(f"Memory limit exceeded for {path_str}")
        except psutil.NoSuchProcess:
            break

        time.sleep(0.1)

    p.join()

    if p.exitcode != 0:
        pytest.skip(f"Process crashed (exit code {p.exitcode}) for {path_str}")

    if result_queue.empty():
        pytest.fail(f"Worker process ended without result for {path_str}")

    status, result = result_queue.get()
    if status == "error":
        raise result

    return result[0], result[1], peak_memory_bytes


def _benchmark_id(val: tuple[str, str, Path]) -> str:
    """Generate a readable test ID for parametrized benchmarks."""
    category, benchmark_name, path = val
    # Get the relative path from category directory to the file
    try:
        category_dir = REPO_ROOT / "benchmarks" / category
        relative_path = path.relative_to(category_dir)
    except ValueError:
        # Fallback if the path is not under the category directory
        return f"{category}/{benchmark_name}/{path.name}"
    else:
        return f"{category}/{relative_path}"


@pytest.mark.benchmark
@pytest.mark.parametrize(
    "benchmark_info",
    collect_qf_lia_benchmark_paths(),
    ids=_benchmark_id,
)
def test_qf_lia_solver_benchmark(benchmark, benchmark_info: tuple[str, str, Path]):
    """Run solver for each .smt2 file from QF_LIA benchmark lists.

    Each .smt2 file is tested individually, so failures are isolated.
    Test IDs show the category, benchmark set name and file name.
    """
    category, benchmark_name, path = benchmark_info

    expected_status, actual_status, peak_memory = benchmark(
        run_in_subprocess, str(path)
    )

    peak_memory_mb = peak_memory / (1024 * 1024)
    benchmark.extra_info["peak_memory_mb"] = f"{peak_memory_mb:.2f} MB"
    benchmark.extra_info["category"] = category
    benchmark.extra_info["benchmark_set"] = benchmark_name

    assert actual_status == expected_status


@pytest.mark.benchmark(
    min_rounds=1,
)
@pytest.mark.parametrize(
    "benchmark_info",
    collect_lia_benchmark_paths(),
    ids=_benchmark_id,
)
def test_lia_solver_benchmark(benchmark, benchmark_info: tuple[str, str, Path]):
    """Run solver for each .smt2 file from LIA benchmark lists.

    Each .smt2 file is tested individually, so failures are isolated.
    Test IDs show the category, benchmark set name and file name.
    """
    category, benchmark_name, path = benchmark_info

    expected_status, actual_status, peak_memory = benchmark(
        run_in_subprocess, str(path)
    )

    peak_memory_mb = peak_memory / (1024 * 1024)
    benchmark.extra_info["peak_memory_mb"] = f"{peak_memory_mb:.2f} MB"
    benchmark.extra_info["category"] = category
    benchmark.extra_info["benchmark_set"] = benchmark_name

    assert actual_status == expected_status
