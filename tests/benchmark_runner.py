import os
import time
import traceback
from multiprocessing import Process, Queue

import psutil
import pytest

from absmt.solver import Solver


def get_memory_limit():
    # 環境変数 BENCHMARK_MEM_LIMIT があれば採用、なければ物理メモリの80%
    # 1. 環境変数をチェック (CLIから渡される想定)
    env_limit = os.getenv("BENCHMARK_MEM_LIMIT")
    if env_limit:
        try:
            return int(env_limit)
        except ValueError:
            pass  # 数値変換できない場合は無視して自動設定へ

    # 2. 指定がなければマシンの物理メモリの 80% を自動設定
    total_mem = psutil.virtual_memory().total
    return int(total_mem * 0.8)


MAX_MEMORY_BYTES = get_memory_limit()


# solver_worker は変更なし
def solver_worker(path_str: str, result_queue: Queue):
    try:
        solver = Solver()
        expected_status = solver.read_from_smtlib(path_str, is_file_path=True)
        actual_status = solver.solve()
        result_queue.put(("ok", (expected_status, actual_status)))
    except Exception as e:  # noqa: BLE001
        error_msg = f"{type(e).__name__}: {e!s}\n{traceback.format_exc()}"
        result_queue.put(("error", error_msg))


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
        time.sleep(0.01)

    p.join()

    if p.exitcode != 0:
        pytest.skip(f"Process crashed (exit code {p.exitcode}) for {path_str}")

    if result_queue.empty():
        pytest.fail(f"Worker process ended without result for {path_str}")

    status, result = result_queue.get()
    if status == "error":
        raise result

    return result[0], result[1], peak_memory_bytes
