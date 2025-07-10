# ruff: noqa: I001, ANN201, LOG015, G004
from absmt.solver import Solver
from absmt.formula.smtlib_reader import SMTLIBReader
import logging
import psutil
import time
from pathlib import Path
import multiprocessing
import os

logging.basicConfig(
    level=logging.INFO,  # INFOレベル以上のログをすべて出力する
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),  # コンソールに出力
    ],
)


# List of SMT2 file paths for indices 2 to 20
PRIME_CONE_SAT = [
    Path(__file__).parent.parent.parent
    / "benchmarks"
    / "QF_LIA"
    / "prime-cone"
    / f"prime_cone_sat_{i}.smt2"
    for i in range(2, 21)
]

PRIME_CONE_UNSAT = [
    Path(__file__).parent.parent.parent
    / "benchmarks"
    / "QF_LIA"
    / "prime-cone"
    / f"prime_cone_unsat_{i}.smt2"
    for i in range(3, 21)
]


def solve_with_timeout(solver: Solver, timeout: int = 60):
    result_queue = multiprocessing.Queue()

    def target() -> None:
        process = psutil.Process(os.getpid())
        max_mem = process.memory_info().rss
        try:
            res = solver.solve()
            max_mem = max(max_mem, process.memory_info().rss)
            result_queue.put((res, max_mem))
        except (RuntimeError, ValueError) as e:
            result_queue.put((e, max_mem))

    p = multiprocessing.Process(target=target)
    p.start()
    p.join(timeout)
    if p.is_alive():
        p.terminate()
        p.join()
        return "timeout", None
    if not result_queue.empty():
        result, max_mem = result_queue.get()
        if isinstance(result, Exception):
            raise result
        return result, max_mem
    return "timeout", None


def main():
    solver = Solver()
    profile_results = []
    reader = SMTLIBReader()

    for smt2_file_path in PRIME_CONE_UNSAT:
        solver.clear()
        status, formula = reader.from_smt_lib(str(smt2_file_path), is_file_path=True)
        solver.add(formula)
        start_time = time.time()

        try:
            result, max_memory_bytes = solve_with_timeout(solver, timeout=60)
            if max_memory_bytes is not None:
                max_memory_mb = max_memory_bytes / (1024 * 1024)
            else:
                max_memory_mb = "N/A"
        except Exception:
            result = "error"
            max_memory_mb = "N/A"
            logging.exception(f"Error occurred for {smt2_file_path.name}")

        end_time = time.time()
        total_time = end_time - start_time

        # Format memory for output
        if isinstance(max_memory_mb, int | float):
            max_memory_str = f"{max_memory_mb:.3f}"
        else:
            max_memory_str = str(max_memory_mb)

        profile_results.append(
            [
                smt2_file_path.name,
                result,
                status,
                f"{total_time:.6f}",
                max_memory_str,
            ]
        )

        if result == "timeout":
            logging.warning(f"Timeout occurred for {smt2_file_path.name}")
        elif result != status:
            logging.error(f"Unexpected result: {result}, expected: {status}")

        logging.info(
            "%-22s %-8s %-8s %10s %10s",
            smt2_file_path.name,
            result,
            status,
            f"{total_time:.6f}",
            max_memory_str,
        )


if __name__ == "__main__":
    main()
