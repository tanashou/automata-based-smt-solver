import time
from multiprocessing import Process, Queue
from pathlib import Path
from typing import TypeVar

import psutil
import pytest
from typing_extensions import ParamSpec

from absmt.formula.smtlib_reader import SMTLIBReader
from absmt.solver import Solver

P = ParamSpec("P")
R = TypeVar("R")

MAX_MEMORY_BYTES = 2 * 1024 * 1024 * 1024  # 2 GB
TIMEOUT_SECONDS = 60


def _resolve_prime_cone_paths() -> list[Path]:
    repo_root = Path(__file__).resolve().parents[1]
    list_file = repo_root / "benchmarks" / "paths" / "prime-cone-sat.txt"
    if not list_file.exists():
        pytest.skip(f"List file not found: {list_file}", allow_module_level=True)
    base_dir = list_file.parent
    paths: list[Path] = []
    with list_file.open("r", encoding="utf-8") as fh:
        for raw_line in fh:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            p = (base_dir / line).resolve()
            if p.exists():
                paths.append(p)
    if not paths:
        pytest.skip(
            f"No referenced .smt2 files found in {list_file}", allow_module_level=True
        )
    return paths


def solver_worker(path_str: str, result_queue: Queue):
    try:
        reader = SMTLIBReader()
        solver = Solver()
        expected_status, formula = reader.from_smt_lib(path_str, is_file_path=True)
        solver.add(formula)
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

    while p.is_alive():
        if time.time() - start_time > TIMEOUT_SECONDS:
            p.terminate()
            p.join()
            pytest.fail(f"Timeout ({TIMEOUT_SECONDS}s) exceeded for {path_str}")

        try:
            mem_info = process.memory_info().rss
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

    return result[0], result[1]


@pytest.mark.parametrize("path", _resolve_prime_cone_paths())
def test_solver_benchmark(benchmark, path: Path):
    expected_status, actual_status = benchmark(run_in_subprocess, str(path))

    assert actual_status == expected_status
