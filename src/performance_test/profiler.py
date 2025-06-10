# ruff: noqa
import subprocess
import sys
import time
from pathlib import Path

import psutil

try:
    # Get the directory of the current script.
    PROFILER_DIR = Path(__file__).parent.resolve()
except NameError:
    # Fallback for cases where __file__ is not defined (e.g., interactive mode).
    PROFILER_DIR = Path.cwd()

TARGET_SCRIPT_PATH = PROFILER_DIR / "target_script.py"

TIMEOUT_SECONDS = 1200


def run_and_profile():
    if not TARGET_SCRIPT_PATH.is_file():
        print(
            f"Error: Target script not found at: {TARGET_SCRIPT_PATH}",
            file=sys.stderr,
        )
        sys.exit(1)

    start_time = time.time()
    max_memory_mb = 0

    # Execute the target script as a child process.
    # `sys.executable` is the path to the current Python interpreter.
    proc = subprocess.Popen(
        [sys.executable, str(TARGET_SCRIPT_PATH)],
        # -----------------
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",  # Specify encoding explicitly.
    )

    p = psutil.Process(proc.pid)
    print(f"Starting process (PID: {proc.pid})... Monitoring begins.")
    print(f"Target: {TARGET_SCRIPT_PATH}")

    try:
        # Loop to monitor the child process.
        while proc.poll() is None:
            # Check for timeout.
            elapsed_time = time.time() - start_time
            if elapsed_time > TIMEOUT_SECONDS:
                print(f"\n--- Timeout ({TIMEOUT_SECONDS} seconds) ---")
                # Kill the child process and all its descendants.
                for child in p.children(recursive=True):
                    child.kill()
                p.kill()
                break

            # Get memory usage (RSS: Resident Set Size).
            try:
                memory_info = p.memory_info()
                current_memory_mb = memory_info.rss / (1024 * 1024)
                max_memory_mb = max(max_memory_mb, current_memory_mb)
            except psutil.NoSuchProcess:
                # In case the process finished between checks.
                break

            # Wait for a short interval.
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nInterrupted manually.")
        p.kill()

    finally:
        # Get the remaining output after the process has finished.
        stdout, stderr = proc.communicate()
        if stdout:
            print(stdout, end="")
        if stderr:
            print(f"Error output: {stderr}", end="", file=sys.stderr)

        # Calculate the final execution time.
        end_time = time.time()
        total_time = end_time - start_time

        # Display the results.
        print("\n--- Profiling Results ---")
        if total_time >= TIMEOUT_SECONDS:
            print("Status: Terminated due to timeout")
        elif proc.returncode != 0:
            print(f"Status: Finished with an error (Exit Code: {proc.returncode})")
        else:
            print("Status: Completed successfully")

        print(f"Execution Time: {total_time:.2f} s")
        print(f"Peak Memory Usage: {max_memory_mb:.2f} MB")

        # Ensure the process is terminated if it's still running.
        if proc.poll() is None:
            proc.kill()


if __name__ == "__main__":
    run_and_profile()
