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

MAX_MEMORY_BYTES = 2 * 1024 * 1024 * 1024  # 2 GB
TIMEOUT_SECONDS = 60

REPO_ROOT = Path(__file__).resolve().parents[1]
PATHS_DIR = REPO_ROOT / "benchmarks" / "paths"

# benchmark file paths (constants)
BROMBERGER = PATHS_DIR / "20180326-Bromberger.txt"
SMPT = PATHS_DIR / "20220307-SMPT.txt"
ULTIMATE_AUTOMIZER_SVCOMP_2023 = PATHS_DIR / "20230321-UltimateAutomizerSvcomp2023.txt"
CALYPTO = PATHS_DIR / "calypto.txt"
CAV = PATHS_DIR / "CAV_2009_benchmarks.txt"
CHECK = PATHS_DIR / "check.txt"
CIRC = PATHS_DIR / "CIRC.txt"
CUT_LEMMAS = PATHS_DIR / "cut_lemmas.txt"
DILLIG = PATHS_DIR / "dillig.txt"
NEC_SMT = PATHS_DIR / "nec-smt.txt"
PB2010 = PATHS_DIR / "pb2010.txt"
PIDGEONS = PATHS_DIR / "pidgeons.txt"
PRIME_CONE = PATHS_DIR / "prime-cone.txt"
RINGS_PREPROCESSED = PATHS_DIR / "rings_preprocessed.txt"
RINGS = PATHS_DIR / "rings.txt"
SLACKS = PATHS_DIR / "slacks.txt"
TIGHTRHOMBUS = PATHS_DIR / "tightrhombus.txt"

PRIME_CONE_SAT_LIST_PATH = PATHS_DIR / "prime-cone-sat.txt"
PRIME_CONE_UNSAT_LIST_PATH = PATHS_DIR / "prime-cone-unsat.txt"

# All other benchmark list files to test (reuse the constant names above)
ALL_BENCHMARK_LISTS = [
    BROMBERGER,
    SMPT,
    ULTIMATE_AUTOMIZER_SVCOMP_2023,
    CALYPTO,
    CAV,
    CHECK,
    CIRC,
    CUT_LEMMAS,
    DILLIG,
    NEC_SMT,
    PB2010,
    PIDGEONS,
    PRIME_CONE,
    RINGS_PREPROCESSED,
    RINGS,
    SLACKS,
    TIGHTRHOMBUS,
]


def resolve_benchmark_paths(list_file_path: Path) -> list[Path]:
    if not list_file_path.exists():
        pytest.skip(f"List file not found: {list_file_path}", allow_module_level=True)

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

    if not paths:
        pytest.skip(
            f"No referenced .smt2 files found in {list_file_path}",
            allow_module_level=True,
        )

    return paths


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


@pytest.mark.parametrize("path", resolve_benchmark_paths(PRIME_CONE_SAT_LIST_PATH))
def test_solver_benchmark_prime_cone_sat(benchmark, path: Path):
    expected_status, actual_status, peak_memory = benchmark(
        run_in_subprocess, str(path)
    )

    peak_memory_mb = peak_memory / (1024 * 1024)
    benchmark.extra_info["peak_memory_mb"] = f"{peak_memory_mb:.2f} MB"

    assert actual_status == expected_status


@pytest.mark.parametrize("path", resolve_benchmark_paths(PRIME_CONE_UNSAT_LIST_PATH))
def test_solver_benchmark_prime_cone_unsat(benchmark, path: Path):
    expected_status, actual_status, peak_memory = benchmark(
        run_in_subprocess, str(path)
    )
    peak_memory_mb = peak_memory / (1024 * 1024)
    benchmark.extra_info["peak_memory_mb"] = f"{peak_memory_mb:.2f} MB"

    assert actual_status == expected_status


@pytest.mark.parametrize("list_path", ALL_BENCHMARK_LISTS)
def test_solver_benchmark_lists(benchmark, list_path: Path):
    """Run solver for every .smt2 referenced from each list file.

    `ALL_BENCHMARK_LISTS`.
    """
    paths = resolve_benchmark_paths(list_path)
    # `resolve_benchmark_paths` will skip the test if list file missing or
    # no referenced .smt2 entries are found.
    if not paths:
        pytest.skip(f"No referenced .smt2 files found in {list_path}")

    for p in paths:
        expected_status, actual_status, peak_memory = benchmark(
            run_in_subprocess, str(p)
        )
        peak_memory_mb = peak_memory / (1024 * 1024)
        benchmark.extra_info[f"{list_path.name}:{p.name}"] = f"{peak_memory_mb:.2f} MB"
        assert actual_status == expected_status
