import time
from multiprocessing import Process, Queue

import psutil
import pytest

from absmt.solver import Solver

MAX_MEMORY_BYTES = 6 * 1024 * 1024 * 1024  # 6 GB


# solver_worker は変更なし
def solver_worker(path_str: str, result_queue: Queue):
    try:
        solver = Solver()
        expected_status = solver.read_from_smtlib(path_str, is_file_path=True)
        actual_status = solver.solve()
        result_queue.put(("ok", (expected_status, actual_status)))
    except Exception as e:  # noqa: BLE001
        result_queue.put(("error", e))


# 引数に timeout を追加し、監視ループ内で時間をチェックします
def run_in_subprocess(path_str: str, timeout: float = 60.0):
    result_queue = Queue()
    p = Process(target=solver_worker, args=(path_str, result_queue))
    p.start()

    # 開始時刻を記録
    start_time = time.time()

    process = psutil.Process(p.pid)
    peak_memory_bytes = 0

    while p.is_alive():
        # --- 追加: タイムアウト判定 ---
        if time.time() - start_time > timeout:
            p.terminate()
            p.join()
            # タイムアウト時は (expected, actual, memory) の形式で返す
            # expected は不明(None), actual は "timeout" とする
            return None, "timeout", peak_memory_bytes
        # ---------------------------

        try:
            mem_info = process.memory_info().rss
            peak_memory_bytes = max(peak_memory_bytes, mem_info)
            if mem_info > MAX_MEMORY_BYTES:
                p.terminate()
                p.join()
                return None, "memout", peak_memory_bytes
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
