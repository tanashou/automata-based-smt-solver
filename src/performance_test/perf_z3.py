# need to run 'pysmt-install --z3' before running this script

# ruff: noqa: C901, PLR0911, PLR0912, PLR0915
import argparse
import logging
import multiprocessing
import time
from pathlib import Path

import psutil
from pysmt.exceptions import SolverReturnedUnknownResultError
from pysmt.shortcuts import Solver, read_smtlib

from performance_test.file_discovery import discover_smt2_files, validate_file
from performance_test.progress_reporter import ProgressReporter

# module logger + configuration
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler()],
)

# Number of sample files to show in debug messages
SAMPLE_PREVIEW = 5


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments for file filtering and directory specification."""
    parser = argparse.ArgumentParser(
        description="Performance testing tool for Z3 solver on SMT2 benchmark files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s  # Process all .smt2 files in default directory
  %(prog)s --pattern "test_*.smt2"  # Process only files matching pattern
  %(prog)s --directory /path/to/benchmarks  # Use custom benchmark directory
  %(prog)s --pattern "*.smt2" --directory ./custom_benchmarks
    """,
    )

    parser.add_argument(
        "--pattern",
        default="*.smt2",
        help="File pattern to match (glob syntax). Default: '*.smt2'",
    )

    parser.add_argument(
        "--directory",
        default=None,
        help="Custom benchmark directory path. Default: benchmarks/LIA/tptp",
    )

    args = parser.parse_args()

    # Validate arguments
    if args.directory and not Path(args.directory).exists():
        parser.error(f"Directory does not exist: {args.directory}")

    # Validate pattern is not empty
    if not args.pattern or not args.pattern.strip():
        parser.error("Pattern cannot be empty")

    return args


def solve_with_timeout_pysmt(
    smt2_path: Path, timeout: int = 60
) -> tuple[str, int | None]:
    result_queue = multiprocessing.Queue()

    def target() -> None:
        process = psutil.Process()
        max_mem = process.memory_info().rss
        try:
            formula = read_smtlib(str(smt2_path))
            with Solver(name="z3", logic=None) as solver:
                solver.add_assertion(formula)
                res = solver.solve()
                max_mem = max(max_mem, process.memory_info().rss)
                if res:
                    result_queue.put(("sat", max_mem))
                else:
                    result_queue.put(("unsat", max_mem))
        except (RuntimeError, ValueError, SolverReturnedUnknownResultError):
            result_queue.put((RuntimeError("solver error"), max_mem))

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


def main() -> None:
    args = parse_arguments()
    progress_reporter = ProgressReporter()

    # Determine the benchmark directory
    if args.directory:
        benchmark_dir = Path(args.directory)
    else:
        benchmark_dir = (
            Path(__file__).parent.parent.parent / "benchmarks" / "LIA" / "tptp"
        )

    # Initialize counters for detailed error tracking
    files_processed = 0
    files_skipped = 0

    try:
        logger.info("Attempting to discover SMT2 files in: %s", benchmark_dir)

        # Dynamically discover SMT2 files with enhanced error handling
        try:
            smt2_files = discover_smt2_files(benchmark_dir, args.pattern)
        except FileNotFoundError:
            logger.exception("Directory discovery failed - directory not found")
            logger.exception(
                "Please check that the benchmark directory exists "
                "and the path is correct",
            )
            return
        except PermissionError:
            logger.exception("Directory discovery failed - permission denied")
            logger.exception(
                "Please check that you have read permissions for "
                "the benchmark directory",
            )
            return
        except NotADirectoryError:
            logger.exception("Directory discovery failed - path is not a directory")
            logger.exception("Please provide a valid directory path")
            return
        except OSError:
            logger.exception("Directory discovery failed - OS error")
            logger.exception(
                "This could be due to network issues, disk problems, "
                "or other system-level issues",
            )
            return
        except Exception:
            logger.exception("Directory discovery failed - unexpected error")
            logger.exception("An unexpected error occurred during file discovery")
            return

        # Handle empty directory case gracefully
        if not smt2_files:
            logger.warning("No SMT2 files found to process")
            logger.info("Processing completed - no files to process")
            return

        logger.info("Successfully discovered %d files for processing", len(smt2_files))

        # Start progress reporting with configuration context
        config_info = {
            "Solver": "Z3 (via PySMT)",
            "Benchmark Directory": str(benchmark_dir),
            "File Pattern": args.pattern,
            "Timeout": "60 seconds",
            "Multiprocessing": "Enabled",
        }
        progress_reporter.report_start(len(smt2_files), config_info)

        # Process each discovered file with enhanced error handling
        for i, smt2_file_path in enumerate(smt2_files, 1):
            progress_reporter.report_progress(i, smt2_file_path.name)

            # Validate file before processing with detailed error handling
            try:
                if not validate_file(smt2_file_path):
                    logger.error(
                        "File validation failed - skipping file: %s",
                        smt2_file_path.name,
                    )
                    progress_reporter.report_file_result(
                        smt2_file_path.name,
                        "error",
                        "unknown",
                        0.0,
                        "N/A",
                        "validation",
                    )
                    files_skipped += 1
                    continue
            except Exception:
                logger.exception("File validation error for %s", smt2_file_path.name)
                progress_reporter.report_file_result(
                    smt2_file_path.name, "error", "unknown", 0.0, "N/A", "validation"
                )
                files_skipped += 1
                continue

            start_time = time.time()

            # Process individual file with comprehensive error handling
            error_type = "general"  # Default error type
            try:
                result, max_memory_bytes = solve_with_timeout_pysmt(
                    smt2_file_path, timeout=60
                )
                if max_memory_bytes is not None:
                    max_memory_mb = max_memory_bytes / (1024 * 1024)
                else:
                    max_memory_mb = "N/A"
            except FileNotFoundError:
                result = "error"
                max_memory_mb = "N/A"
                error_type = "parsing"
                logger.exception(
                    "Z3 solver error - file not found during solving: %s",
                    smt2_file_path.name,
                )
            except PermissionError:
                result = "error"
                max_memory_mb = "N/A"
                error_type = "parsing"
                logger.exception(
                    "Z3 solver error - permission denied: %s",
                    smt2_file_path.name,
                )
            except MemoryError:
                result = "error"
                max_memory_mb = "N/A"
                error_type = "solver"
                logger.exception(
                    "Z3 solver error - out of memory while solving %s",
                    smt2_file_path.name,
                )
            except SolverReturnedUnknownResultError:
                result = "unknown"
                max_memory_mb = "N/A"
                logger.warning(
                    "Z3 solver returned unknown result for %s",
                    smt2_file_path.name,
                )
            except (RuntimeError, ValueError):
                result = "error"
                max_memory_mb = "N/A"
                error_type = "solver"
                logger.exception(
                    "Z3 solver error - runtime/value error for %s",
                    smt2_file_path.name,
                )
            except Exception:
                result = "error"
                max_memory_mb = "N/A"
                error_type = "solver"
                logger.exception(
                    "Z3 solver error - unexpected error for %s",
                    smt2_file_path.name,
                )

            end_time = time.time()
            total_time = end_time - start_time

            # Format memory for output
            if isinstance(max_memory_mb, int | float):
                max_memory_str = f"{max_memory_mb:.3f}"
            else:
                max_memory_str = str(max_memory_mb)

            # Log specific result types
            if result == "timeout":
                logger.warning(
                    "Z3 solver timeout occurred for %s after %.2f seconds",
                    smt2_file_path.name,
                    total_time,
                )
            elif result == "error":
                logger.error("Z3 solver error occurred for %s", smt2_file_path.name)
            elif result == "unknown":
                logger.info("Z3 solver returned unknown for %s", smt2_file_path.name)

            # Report file result (Z3 doesn't have expected status, so use "unknown")
            if result == "error":
                progress_reporter.report_file_result(
                    smt2_file_path.name,
                    result,
                    "unknown",
                    total_time,
                    max_memory_str,
                    error_type,
                )
            else:
                progress_reporter.report_file_result(
                    smt2_file_path.name, result, "unknown", total_time, max_memory_str
                )

            if result != "error":
                files_processed += 1
            else:
                files_skipped += 1

        # Report final summary with additional statistics
        logger.info(
            "Processing completed: %d files processed successfully, %d files skipped",
            files_processed,
            files_skipped,
        )
        progress_reporter.report_summary()

    except KeyboardInterrupt:
        logger.warning("Processing interrupted by user (Ctrl+C)")
        logger.info(
            "Partial results: %d files processed, %d files skipped",
            files_processed,
            files_skipped,
        )
        return
    except Exception:
        logger.exception("Critical error during benchmark processing")
        logger.exception(
            "This indicates a serious problem with the processing pipeline",
        )
        return


if __name__ == "__main__":
    main()
