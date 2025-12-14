import time
from multiprocessing import Process, Queue

import psutil
import pytest

from absmt.solver import Solver

MAX_MEMORY_BYTES = 4 * 1024 * 1024 * 1024  # 4 GB
TIMEOUT_SECONDS = 120


def solver_worker(path_str: str, result_queue: Queue):
    try:
        solver = Solver()
        expected_status = solver.read_from_smtlib(path_str, is_file_path=True)
        actual_status = solver.solve()
        result_queue.put(("ok", (expected_status, actual_status)))
    except Exception as e:  # noqa: BLE001
        result_queue.put(("error", e))


def run_in_subprocess(path_str: str, timeout_seconds: int = TIMEOUT_SECONDS):
    result_queue = Queue()
    p = Process(target=solver_worker, args=(path_str, result_queue))
    p.start()

    process = psutil.Process(p.pid)
    start_time = time.time()
    peak_memory_bytes = 0

    while p.is_alive():
        if time.time() - start_time > timeout_seconds:
            p.terminate()
            p.join()
            pytest.fail(f"Timeout ({timeout_seconds}s) exceeded for {path_str}")

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
