import argparse
import logging
import multiprocessing
import os
import sys
import time
from pathlib import Path
from typing import Any

import psutil
# ruff: noqa: C901,PLR0911,PLR0912,PLR0915,PLR2004,BLE001,TRY401,F841,E501,I001

from absmt.formula.smtlib_reader import SMTLIBReader
from absmt.solver import Solver
from performance_test.file_discovery import discover_smt2_files, validate_file
from performance_test.progress_reporter import ProgressReporter

# Use a module-level logger and parameterized logging to satisfy linter rules
logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,  # INFOレベル以上のログをすべて出力する
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),  # コンソールに出力
    ],
)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments for file filtering and directory specification."""
    parser = argparse.ArgumentParser(
        description="Performance testing tool for AbSMT solver on SMT2 benchmark files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Process all .smt2 files in default directory
  %(prog)s --pattern "test_*.smt2"           # Process only files matching pattern
  %(prog)s --directory /path/to/benchmarks   # Use custom benchmark directory
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


def solve_with_timeout(solver: Solver, timeout: int = 60) -> tuple[Any, int | None]:
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


def main() -> None:
    args = parse_arguments()
    solver = Solver()
    reader = SMTLIBReader()
    progress_reporter = ProgressReporter()

    # Determine the benchmark directory
    if args.directory:
        benchmark_dir = Path(args.directory)
    else:
        benchmark_dir = (
            Path(__file__).parent.parent.parent / "benchmarks" / "QF_LIA" / "prime-cone"
        )

    # Initialize counters for detailed error tracking
    files_processed = 0
    files_skipped = 0
    discovery_errors = 0

    try:
        logger.info("Attempting to discover SMT2 files in: %s", benchmark_dir)
        logger.info("Using file pattern: %s", args.pattern)
        logger.info("Directory path resolved to: %s", benchmark_dir.resolve())

        # Dynamically discover SMT2 files with comprehensive error handling
        try:
            smt2_files = discover_smt2_files(benchmark_dir, args.pattern)

        except FileNotFoundError:
            logger.exception("Directory discovery failed - directory not found")
            logger.exception("Troubleshooting steps:")
            logger.exception("  1. Verify the benchmark directory exists")
            logger.exception("  2. Check the directory path is correct")
            logger.exception("  3. Ensure the directory hasn't been moved or deleted")
            logger.exception("  4. Current working directory: %s", Path.cwd())
            logger.exception("  5. Attempted path: %s", benchmark_dir)
            return

        except PermissionError:
            logger.exception("Directory discovery failed - permission denied")
            logger.exception("Troubleshooting steps:")
            logger.exception("  1. Check read permissions for the benchmark directory")
            logger.exception("  2. Run with appropriate user privileges")
            logger.exception(
                "  3. Verify directory is not restricted by system policies"
            )
            logger.exception("  4. Check parent directory permissions")
            return

        except NotADirectoryError:
            logger.exception("Directory discovery failed - path is not a directory")
            logger.exception("Troubleshooting steps:")
            logger.exception("  1. Verify the path points to a directory, not a file")
            logger.exception("  2. Check if the path is a symbolic link to a file")
            logger.exception("  3. Ensure the path doesn't contain invalid characters")
            return

        except ValueError:
            logger.exception("Directory discovery failed - invalid pattern")
            logger.exception("Troubleshooting steps:")
            logger.exception("  1. Check the file pattern syntax")
            logger.exception("  2. Ensure the pattern uses valid glob syntax")
            logger.exception("  3. Current pattern: '%s'", args.pattern)
            logger.exception(
                "  4. Example valid patterns: '*.smt2', '**/*.smt2', 'test_*.smt2'"
            )
            return

        except OSError:
            logger.exception("Directory discovery failed - OS error")
            logger.exception("This indicates a system-level issue:")
            logger.exception("  - Network connectivity problems (for remote paths)")
            logger.exception("  - File system corruption or errors")
            logger.exception("  - Resource exhaustion (disk space, memory)")
            logger.exception("  - Hardware issues with storage device")
            logger.exception("Recommended actions:")
            logger.exception("  1. Check system logs for related errors")
            logger.exception("  2. Verify disk space and file system health")
            logger.exception("  3. Try accessing the directory manually")
            return

        except RuntimeError:
            logger.exception("Directory discovery failed - internal error")
            logger.exception(
                "This indicates an internal error in the file discovery system"
            )
            logger.exception("Please report this issue with the following information:")
            logger.exception("  - Python version: %s", sys.version)
            logger.exception("  - Operating system: %s", os.name)
            logger.exception("  - Directory path: %s", benchmark_dir)
            logger.exception("  - Pattern: %s", args.pattern)
            return

        except Exception:
            logger.exception("Directory discovery failed - unexpected error")
            logger.exception("An unexpected error occurred during file discovery")
            logger.exception("This is likely a bug in the file discovery system")
            logger.exception("Please report this issue with the full error details")
            return

        # Handle empty directory case gracefully with enhanced information
        if not smt2_files:
            logger.warning("No SMT2 files found to process")
            logger.info("This could be due to:")
            logger.info("  - Empty benchmark directory")
            logger.info("  - No files matching pattern '%s'", args.pattern)
            logger.info("  - All files filtered out during validation")
            logger.info("Processing completed - no files to process")

            # Provide helpful suggestions
            try:
                if benchmark_dir.exists() and benchmark_dir.is_dir():
                    all_files = list(benchmark_dir.iterdir())
                    if all_files:
                        logger.info("Directory contains %d items", len(all_files))
                        sample_files = [f.name for f in all_files[:5] if f.is_file()]
                        if sample_files:
                            logger.info("Sample files found: %s", sample_files)
                        else:
                            logger.info(
                                "Directory contains subdirectories but no files"
                            )
                    else:
                        logger.info("Directory is completely empty")
            except OSError as check_e:
                logger.debug("Could not analyze directory contents: %s", check_e)

            return

        logger.info("Successfully discovered %d files for processing", len(smt2_files))
        logger.debug("First few files: %s", [f.name for f in smt2_files[:5]])
        if len(smt2_files) > 5:
            logger.debug("... and %d more files", len(smt2_files) - 5)

        # Start progress reporting with configuration context
        config_info = {
            "Solver": "AbSMT",
            "Benchmark Directory": str(benchmark_dir),
            "File Pattern": args.pattern,
            "Timeout": "300 seconds",
            "Python Version": sys.version.split()[0],
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

            # Process individual file with comprehensive error handling
            try:
                # Parse SMT-LIB file
                try:
                    status, formula = reader.from_smt_lib(
                        str(smt2_file_path), is_file_path=True
                    )
                except FileNotFoundError:
                    logger.exception(
                        "File parsing failed - file not found during parsing: %s",
                        smt2_file_path.name,
                    )
                    progress_reporter.report_file_result(
                        smt2_file_path.name, "error", "unknown", 0.0, "N/A", "parsing"
                    )
                    files_skipped += 1
                    continue
                except PermissionError:
                    logger.exception(
                        "File parsing failed - permission denied: %s",
                        smt2_file_path.name,
                    )
                    progress_reporter.report_file_result(
                        smt2_file_path.name, "error", "unknown", 0.0, "N/A", "parsing"
                    )
                    files_skipped += 1
                    continue
                except (ValueError, SyntaxError):
                    logger.exception(
                        "File parsing failed - invalid SMT-LIB syntax in %s",
                        smt2_file_path.name,
                    )
                    progress_reporter.report_file_result(
                        smt2_file_path.name, "error", "unknown", 0.0, "N/A", "parsing"
                    )
                    files_skipped += 1
                    continue
                except Exception:
                    logger.exception(
                        "File parsing failed - unexpected error parsing %s",
                        smt2_file_path.name,
                    )
                    progress_reporter.report_file_result(
                        smt2_file_path.name, "error", "unknown", 0.0, "N/A", "parsing"
                    )
                    files_skipped += 1
                    continue

                # Add formula to solver
                try:
                    solver.add(formula)
                except Exception:
                    logger.exception(
                        "Solver error - failed to add formula from %s",
                        smt2_file_path.name,
                    )
                    progress_reporter.report_file_result(
                        smt2_file_path.name, "error", "unknown", 0.0, "N/A", "solver"
                    )
                    # Try to clear solver state
                    try:
                        solver.clear()
                    except Exception:
                        logger.warning(
                            "Failed to clear solver state after error with %s",
                            smt2_file_path.name,
                        )
                    files_skipped += 1
                    continue

                start_time = time.time()

                # Solve with timeout and comprehensive error handling
                error_type = "general"  # Default error type
                try:
                    result, max_memory_bytes = solve_with_timeout(solver, timeout=300)
                    if max_memory_bytes is not None:
                        max_memory_mb = max_memory_bytes / (1024 * 1024)
                    else:
                        max_memory_mb = "N/A"
                except MemoryError:
                    result = "error"
                    max_memory_mb = "N/A"
                    error_type = "solver"
                    logger.exception(
                        "Solver error - out of memory while solving %s",
                        smt2_file_path.name,
                    )
                except RuntimeError:
                    result = "error"
                    max_memory_mb = "N/A"
                    error_type = "solver"
                    logger.exception(
                        "Solver error - runtime error solving %s", smt2_file_path.name
                    )
                except Exception:
                    result = "error"
                    max_memory_mb = "N/A"
                    error_type = "solver"
                    logger.exception(
                        "Solver error - unexpected error solving %s",
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
                        "Solver timeout occurred for %s after %.2f seconds",
                        smt2_file_path.name,
                        total_time,
                    )
                elif result == "error":
                    logger.error("Solver error occurred for %s", smt2_file_path.name)
                elif result != status:
                    logger.warning(
                        "Result mismatch for %s: got %s, expected %s",
                        smt2_file_path.name,
                        result,
                        status,
                    )

                # Report file result
                if result == "error":
                    progress_reporter.report_file_result(
                        smt2_file_path.name,
                        result,
                        status,
                        total_time,
                        max_memory_str,
                        error_type,
                    )
                else:
                    progress_reporter.report_file_result(
                        smt2_file_path.name, result, status, total_time, max_memory_str
                    )

                files_processed += 1

                # Clear solver state with error handling
                try:
                    solver.clear()
                except Exception as e:
                    logger.warning(
                        "Failed to clear solver state after processing %s: %s",
                        smt2_file_path.name,
                        e,
                    )

            except Exception as e:
                logger.exception(
                    "Unexpected error processing file %s: %s", smt2_file_path.name, e
                )
                progress_reporter.report_file_result(
                    smt2_file_path.name, "error", "unknown", 0.0, "N/A", "general"
                )
                files_skipped += 1
                # Clear solver state even on error
                try:
                    solver.clear()
                except Exception as cleanup_e:
                    logger.warning(
                        "Failed to clear solver state after error with %s: %s",
                        smt2_file_path.name,
                        cleanup_e,
                    )

        # Report final summary with additional statistics
        logger.info(
            "Processing completed: %d files processed successfully, %d files skipped",
            files_processed,
            files_skipped,
        )
        summary = progress_reporter.report_summary()

    except KeyboardInterrupt:
        logger.warning("Processing interrupted by user (Ctrl+C)")
        logger.info(
            "Partial results: %d files processed, %d files skipped",
            files_processed,
            files_skipped,
        )
        return
    except Exception as e:
        logger.exception("Critical error during benchmark processing: %s", e)
        logger.exception(
            "This indicates a serious problem with the processing pipeline"
        )
        return


if __name__ == "__main__":
    main()
