"""Progress reporting functionality for benchmark processing."""

import logging
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Magic constants
TIMEOUT_THRESHOLD = 300  # seconds
LONG_PROCESSING_TIME = 60  # seconds
VERY_FAST_PROCESSING_TIME = 0.001  # seconds
QUICK_FAILURE_TIME = 0.1  # seconds
HIGH_MEMORY_USAGE = 1000  # MB
LOW_MEMORY_USAGE = 10  # MB
CRITICAL_ERROR_RATE = 50  # percent
WARNING_ERROR_RATE = 20  # percent
HIGH_TIMEOUT_RATE = 30  # percent
EXCELLENT_SUCCESS_RATE = 80  # percent
GOOD_SUCCESS_RATE = 60  # percent
DISPLAY_FILENAME_MAX = 22
DISPLAY_FILENAME_TRUNC = 19
DISPLAY_MEMORY_MAX = 10
DISPLAY_MEMORY_TRUNC = 7
ETA_MIN_SECONDS = 60


@dataclass
class ProcessingSummary:
    """Summary statistics for benchmark processing."""

    total_files: int
    processed_files: int
    successful: int
    errors: int
    timeouts: int
    total_time: float
    # Enhanced statistics
    result_mismatches: int = 0
    parsing_errors: int = 0
    solver_errors: int = 0
    validation_errors: int = 0
    general_errors: int = 0
    min_processing_time: float = 0.0
    max_processing_time: float = 0.0
    avg_processing_time: float = 0.0
    total_memory_usage: float = 0.0
    avg_memory_usage: float = 0.0
    files_per_second: float = 0.0
    # Additional detailed statistics
    sat_results: int = 0
    unsat_results: int = 0
    unknown_results: int = 0
    fastest_file: str = ""
    slowest_file: str = ""
    highest_memory_file: str = ""
    most_problematic_error_type: str = ""


class ProgressReporter:
    """Progress reporter for benchmark file processing.

    Provides methods for reporting start, progress, and summary information
    during benchmark processing operations.
    """

    def __init__(self) -> None:
        """Initialize the progress reporter."""
        self._start_time: float | None = None
        self._total_files: int = 0
        self._processed_files: int = 0
        self._successful: int = 0
        self._errors: int = 0
        self._timeouts: int = 0
        # Enhanced tracking
        self._result_mismatches: int = 0
        self._parsing_errors: int = 0
        self._solver_errors: int = 0
        self._validation_errors: int = 0
        self._general_errors: int = 0
        self._processing_times: list[float] = []
        self._memory_usages: list[float] = []
        # Additional detailed tracking
        self._sat_results: int = 0
        self._unsat_results: int = 0
        self._unknown_results: int = 0
        self._file_performance: list[
            tuple[str, float, str]
        ] = []  # (filename, time, memory)
        self._error_details: dict[str, int] = {}  # error_type -> count

    # --- Helper methods to keep main methods small ---
    def _log_table_row(
        self,
        filename: str,
        result: str,
        expected_status: str,
        execution_time: float,
        memory_usage: str,
    ) -> None:
        """Log a formatted table row for a single file result."""
        display_filename = (
            filename
            if len(filename) <= DISPLAY_FILENAME_MAX
            else filename[:DISPLAY_FILENAME_TRUNC] + "..."
        )

        display_memory = (
            memory_usage
            if len(str(memory_usage)) <= DISPLAY_MEMORY_MAX
            else str(memory_usage)[:DISPLAY_MEMORY_TRUNC] + "..."
        )
        try:
            logger.info(
                "%-22s %-8s %-8s %10.6f %10s",
                display_filename,
                result,
                expected_status,
                execution_time,
                display_memory,
            )
        except (ValueError, TypeError):
            logger.info(
                "Result: %s -> %s (expected: %s) in %.6fs, memory: %s",
                filename,
                result,
                expected_status,
                execution_time,
                memory_usage,
            )

    def _handle_timeout(self, filename: str, execution_time: float) -> None:
        self._timeouts += 1
        logger.debug("File %s timed out after %.2f seconds", filename, execution_time)
        if execution_time > TIMEOUT_THRESHOLD:
            logger.info("Long timeout detected for %s: %.2fs", filename, execution_time)

    def _handle_error(
        self,
        filename: str,
        execution_time: float,
        error_type: str,
    ) -> None:
        self._errors += 1
        if error_type == "parsing":
            self._parsing_errors += 1
            logger.debug(
                "File %s failed with parsing error after %.2f seconds",
                filename,
                execution_time,
            )
        elif error_type == "solver":
            self._solver_errors += 1
            logger.debug(
                "File %s failed with solver error after %.2f seconds",
                filename,
                execution_time,
            )
        elif error_type == "validation":
            self._validation_errors += 1
            logger.debug(
                "File %s failed with validation error after %.2f seconds",
                filename,
                execution_time,
            )
        else:
            self._general_errors += 1
            logger.debug(
                "File %s failed with general error after %.2f seconds",
                filename,
                execution_time,
            )
        self._error_details[error_type] = self._error_details.get(error_type, 0) + 1
        if execution_time < QUICK_FAILURE_TIME:
            logger.debug(
                "Quick failure for %s suggests parsing or validation error",
                filename,
            )
        elif execution_time > LONG_PROCESSING_TIME:
            logger.debug(
                "Long processing time before error for %s suggests solver issue",
                filename,
            )

    def _handle_success(
        self,
        filename: str,
        result: str,
        expected_status: str,
        execution_time: float,
        memory_usage: str,
    ) -> None:
        self._successful += 1
        logger.debug(
            "File %s processed successfully: %s in %.2fs",
            filename,
            result,
            execution_time,
        )
        if result == "sat":
            self._sat_results += 1
        elif result == "unsat":
            self._unsat_results += 1
        elif result == "unknown":
            self._unknown_results += 1

        if result != expected_status and expected_status not in ["unknown", ""]:
            self._result_mismatches += 1
            logger.warning(
                "Result mismatch for %s: got '%s', expected '%s'",
                filename,
                result,
                expected_status,
            )
            logger.debug("Possible causes:")
            logger.debug("  - Different solver behavior")
            logger.debug("  - Incorrect expected result in benchmark")
            logger.debug("  - Solver timeout leading to different result")

        if execution_time > LONG_PROCESSING_TIME:
            logger.info("Long processing time for %s: %.2fs", filename, execution_time)
        elif execution_time < VERY_FAST_PROCESSING_TIME:
            logger.debug("Very fast processing for %s: %.6fs", filename, execution_time)

        self._processing_times.append(execution_time)
        self._file_performance.append((filename, execution_time, memory_usage))
        if memory_usage != "N/A" and isinstance(memory_usage, str):
            try:
                memory_val = float(memory_usage)
            except (ValueError, TypeError):
                memory_val = None
            if memory_val is not None:
                self._memory_usages.append(memory_val)

    def _validate_file_result(
        self,
        filename: str,
        result: str,
        expected_status: str,
        execution_time: float,
        memory_usage: str,
    ) -> tuple[str, str, str, float, str]:
        """Validate and normalize inputs for report_file_result."""
        if not isinstance(filename, str) or not filename.strip():
            logger.error(
                "Invalid filename provided to report_file_result: %r",
                filename,
            )
            filename = "INVALID_FILENAME"
        if not isinstance(result, str):
            logger.error(
                "Invalid result type provided: %s for file %s",
                type(result),
                filename,
            )
            result = "error"
        if not isinstance(expected_status, str):
            logger.warning(
                "Invalid expected_status type provided: %s for file %s",
                type(expected_status),
                filename,
            )
            expected_status = "unknown"
        if not isinstance(execution_time, int | float) or execution_time < 0:
            logger.warning(
                "Invalid execution_time provided: %s for file %s",
                execution_time,
                filename,
            )
            execution_time = 0.0
        if not isinstance(memory_usage, str):
            logger.warning(
                "Invalid memory_usage type provided: %s for file %s",
                type(memory_usage),
                filename,
            )
            memory_usage = "N/A"
        return filename, result, expected_status, execution_time, memory_usage

    def report_start(self, total_files: int, config_info: dict | None = None) -> None:
        """Report the start of processing with total file count and configuration.

        Args:
            total_files: Total number of files to be processed
            config_info: Optional configuration information to include in the report

        """
        self._start_time = time.time()
        self._total_files = total_files
        self._processed_files = 0
        self._successful = 0
        self._errors = 0
        self._timeouts = 0
        # Reset enhanced tracking
        self._parsing_errors = 0
        self._solver_errors = 0
        self._validation_errors = 0
        self._general_errors = 0
        self._processing_times = []
        self._memory_usages = []
        # Reset additional detailed tracking
        self._sat_results = 0
        self._unsat_results = 0
        self._unknown_results = 0
        self._file_performance = []
        self._error_details = {}

        logger.info(
            "Starting benchmark processing: %d files to process",
            total_files,
        )
        logger.info(
            "Processing started at: %s",
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self._start_time)),
        )
        logger.info("=" * 70)
        logger.info("PROCESSING CONTEXT:")
        logger.info("  - Total files to process: %d", total_files)
        logger.info("  - Processing mode: Individual file validation and solving")
        logger.info("  - Timeout handling: Enabled with multiprocessing")
        logger.info("  - Memory tracking: Enabled")
        logger.info("  - Error recovery: Continue on individual file failures")

        # Add configuration information if provided
        if config_info:
            logger.info("CONFIGURATION:")
            for key, value in config_info.items():
                logger.info("  - %s: %s", key, value)

        logger.info("=" * 70)
        logger.info(
            "%-22s %-8s %-8s %10s %10s",
            "Filename",
            "Result",
            "Expected",
            "Time(s)",
            "Memory(MB)",
        )
        logger.info("-" * 70)

    def report_progress(self, current: int, filename: str) -> None:
        """Report progress for the current file being processed.

        Args:
            current: Current file number (1-based)
            filename: Name of the file being processed

        """
        self._processed_files = current

        # Calculate progress percentage and estimated completion time
        progress_pct = (
            (current / self._total_files) * 100 if self._total_files > 0 else 0
        )

        # Estimate completion time based on current progress
        if self._start_time and current > 1:
            elapsed_time = time.time() - self._start_time
            avg_time_per_file = elapsed_time / (current - 1)
            remaining_files = self._total_files - current + 1
            estimated_remaining_time = avg_time_per_file * remaining_files
            if estimated_remaining_time > ETA_MIN_SECONDS:
                eta_str = f"ETA: {estimated_remaining_time / 60:.1f}m"
            else:
                eta_str = f"ETA: {round(estimated_remaining_time)}s"
        else:
            eta_str = "ETA: calculating..."

        logger.info(
            "Processing file %d/%d (%.1f%%) - %s: %s",
            current,
            self._total_files,
            progress_pct,
            eta_str,
            filename,
        )

        # Log milestone progress
        if (
            current in [1, 10, 25, 50, 100]
            or current % 100 == 0
            or current == self._total_files
        ):
            logger.info(
                "MILESTONE: Reached file %d of %d (%.1f%% complete)",
                current,
                self._total_files,
                progress_pct,
            )

    def report_file_result(
        self,
        filename: str,
        result: str,
        expected_status: str,
        execution_time: float,
        memory_usage: str,
        error_type: str = "general",
    ) -> None:
        """Report the result of processing a single file.

        Args:
            filename: Name of the processed file
            result: Processing result (sat/unsat/timeout/error/unknown)
            expected_status: Expected result status
            execution_time: Time taken to process the file
            memory_usage: Memory usage during processing
            error_type: Type of error if result is "error"
                (parsing/solver/validation/general)

        """
        # Validate and normalize inputs
        filename, result, expected_status, execution_time, memory_usage = (
            self._validate_file_result(
                filename, result, expected_status, execution_time, memory_usage
            )
        )

        # Dispatch to specialized handlers to reduce branching complexity
        if result == "timeout":
            self._handle_timeout(filename, execution_time)
        elif result == "error":
            self._handle_error(filename, execution_time, error_type)
        elif result in ("sat", "unsat", "unknown"):
            self._handle_success(
                filename,
                result,
                expected_status,
                execution_time,
                memory_usage,
            )
        else:
            logger.warning("Unexpected result type '%s' for file %s", result, filename)
            logger.warning(
                "Valid result types are: sat, unsat, unknown, timeout, error"
            )
            logger.debug("Result will be categorized as error for statistics")
            self._errors += 1
            result = "error"
        # Table row logging is handled inside _log_table_row
        # Log final table row
        self._log_table_row(
            filename, result, expected_status, execution_time, memory_usage
        )

    def report_summary(self) -> ProcessingSummary:
        """Report final processing summary and return summary statistics.

        Returns:
            ProcessingSummary object with complete statistics

        """
        # Build the summary; if creation fails return a minimal summary
        try:
            summary = self._create_summary()
        except Exception:  # pragma: no cover - defensive
            logger.exception("Critical error creating processing summary")
            logger.exception("Returning minimal summary due to internal error")
            return ProcessingSummary(
                total_files=0,
                processed_files=0,
                successful=0,
                errors=1,
                timeouts=0,
                total_time=0.0,
                parsing_errors=0,
                solver_errors=0,
                validation_errors=0,
                general_errors=1,
                min_processing_time=0.0,
                max_processing_time=0.0,
                avg_processing_time=0.0,
                total_memory_usage=0.0,
                avg_memory_usage=0.0,
                sat_results=0,
                unsat_results=0,
                unknown_results=0,
                fastest_file="",
                slowest_file="",
                highest_memory_file="",
                most_problematic_error_type="general",
            )

        # Log the summary; protect logging from raising
        try:
            self._log_summary(summary)
        except Exception:  # pragma: no cover - defensive
            logger.exception("Error logging processing summary")

        return summary

    def _create_summary(self) -> ProcessingSummary:
        """Create ProcessingSummary from collected stats."""
        # Calculate total time
        if self._start_time is None:
            total_time = 0.0
            logger.warning("Summary requested but processing was never started")
            logger.debug("This could indicate an error in the processing workflow")
        else:
            try:
                total_time = time.time() - self._start_time
                if total_time < 0:
                    logger.warning("Negative total time calculated: %s", total_time)
                    logger.debug(
                        "This could indicate system clock changes during processing"
                    )
                    total_time = 0.0
            except Exception:  # pragma: no cover - defensive
                logger.exception("Error calculating total processing time")
                total_time = 0.0

        min_time = min(self._processing_times) if self._processing_times else 0.0
        max_time = max(self._processing_times) if self._processing_times else 0.0
        avg_time = (
            sum(self._processing_times) / len(self._processing_times)
            if self._processing_times
            else 0.0
        )
        total_memory = sum(self._memory_usages) if self._memory_usages else 0.0
        avg_memory = (
            total_memory / len(self._memory_usages) if self._memory_usages else 0.0
        )

        fastest_file = ""
        slowest_file = ""
        highest_memory_file = ""
        if self._file_performance:
            fastest_file = min(self._file_performance, key=lambda x: x[1])[0]
            slowest_file = max(self._file_performance, key=lambda x: x[1])[0]
            memory_files = [(f, m) for f, _, m in self._file_performance if m != "N/A"]
            if memory_files:
                try:
                    highest_memory_file = max(
                        memory_files,
                        key=lambda x: float(x[1]),
                    )[0]
                except (ValueError, TypeError):
                    highest_memory_file = ""

        most_problematic_error_type = ""
        if self._error_details:
            most_problematic_error_type = max(
                self._error_details.items(), key=lambda x: x[1]
            )[0]

        summary = ProcessingSummary(
            total_files=max(0, self._total_files),
            processed_files=max(0, self._processed_files),
            successful=max(0, self._successful),
            errors=max(0, self._errors),
            timeouts=max(0, self._timeouts),
            total_time=max(0.0, total_time),
            result_mismatches=max(0, self._result_mismatches),
            parsing_errors=max(0, self._parsing_errors),
            solver_errors=max(0, self._solver_errors),
            validation_errors=max(0, self._validation_errors),
            general_errors=max(0, self._general_errors),
            min_processing_time=max(0.0, min_time),
            max_processing_time=max(0.0, max_time),
            avg_processing_time=max(0.0, avg_time),
            total_memory_usage=max(0.0, total_memory),
            avg_memory_usage=max(0.0, avg_memory),
            sat_results=max(0, self._sat_results),
            unsat_results=max(0, self._unsat_results),
            unknown_results=max(0, self._unknown_results),
            fastest_file=fastest_file,
            slowest_file=slowest_file,
            highest_memory_file=highest_memory_file,
            most_problematic_error_type=most_problematic_error_type,
        )

        # Log potential inconsistency
        calculated_total = summary.successful + summary.errors + summary.timeouts
        if calculated_total != summary.processed_files:
            logger.warning(
                "Summary inconsistency detected: successful(%d) + errors(%d) + "
                "timeouts(%d) = %d != processed_files(%d)",
                summary.successful,
                summary.errors,
                summary.timeouts,
                calculated_total,
                summary.processed_files,
            )

        return summary

    def _log_summary(self, summary: ProcessingSummary) -> None:
        # Delegate logging to smaller helpers to reduce complexity
        self._log_overview(summary)
        self._log_breakdown(summary)
        self._log_performance(summary)
        self._log_analysis(summary)
        logger.info("=" * 70)
        logger.info("BENCHMARK PROCESSING COMPLETED")
        if summary.successful > 0:
            logger.info("\u2705 Successfully processed %d files", summary.successful)
        if summary.errors > 0:
            logger.info("\u2717 %d files encountered errors", summary.errors)
        if summary.timeouts > 0:
            logger.info("\u23f1 %d files timed out", summary.timeouts)

    def _log_overview(self, summary: ProcessingSummary) -> None:
        logger.info("-" * 70)
        logger.info("FINAL PROCESSING SUMMARY:")
        logger.info(
            "Processing completed at: %s",
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        )
        logger.info("Session duration: %.2f seconds", summary.total_time)
        logger.info("")
        logger.info("FILE PROCESSING RESULTS:")
        logger.info("  Total files discovered: %d", summary.total_files)
        logger.info("  Files processed: %d", summary.processed_files)
        logger.info("  Successful results: %d", summary.successful)
        logger.info("  Errors encountered: %d", summary.errors)
        if summary.errors > 0:
            logger.info("    - Parsing errors: %d", summary.parsing_errors)
            logger.info("    - Solver errors: %d", summary.solver_errors)
            logger.info("    - Validation errors: %d", summary.validation_errors)
            logger.info("    - General errors: %d", summary.general_errors)
            if summary.most_problematic_error_type:
                logger.info(
                    "    - Most common error type: %s",
                    summary.most_problematic_error_type,
                )
        logger.info("  Timeouts occurred: %d", summary.timeouts)
        logger.info("  Total processing time: %.2f seconds", summary.total_time)

    def _log_breakdown(self, summary: ProcessingSummary) -> None:
        if summary.successful > 0:
            logger.info("  Result breakdown:")
            logger.info("    - SAT results: %d", summary.sat_results)
            logger.info("    - UNSAT results: %d", summary.unsat_results)
            logger.info("    - UNKNOWN results: %d", summary.unknown_results)
            if summary.result_mismatches > 0:
                logger.info("    - Result mismatches: %d", summary.result_mismatches)

        if summary.fastest_file and summary.slowest_file:
            logger.info("  Performance highlights:")
            logger.info(
                "    - Fastest file: %s (%.6fs)",
                summary.fastest_file,
                summary.min_processing_time,
            )
            logger.info(
                "    - Slowest file: %s (%.2fs)",
                summary.slowest_file,
                summary.max_processing_time,
            )
            if summary.highest_memory_file:
                logger.info(
                    "    - Highest memory usage: %s",
                    summary.highest_memory_file,
                )

    def _log_performance(self, summary: ProcessingSummary) -> None:
        if summary.total_files <= 0:
            logger.warning("No files were processed")
            logger.debug("This could indicate:")
            logger.debug("  - Empty directory")
            logger.debug("  - File discovery failures")
            logger.debug("  - All files failed validation")
            return

        try:
            success_rate = (summary.successful / summary.total_files) * 100
            error_rate = (summary.errors / summary.total_files) * 100
            timeout_rate = (summary.timeouts / summary.total_files) * 100

            logger.info("  Success rate: %.1f%%", success_rate)
            logger.info("  Error rate: %.1f%%", error_rate)
            logger.info("  Timeout rate: %.1f%%", timeout_rate)

            if summary.avg_processing_time > 0:
                logger.info(
                    "  Average time per file: %.2f seconds",
                    summary.avg_processing_time,
                )
                logger.info(
                    "  Minimum processing time: %.2f seconds",
                    summary.min_processing_time,
                )
                logger.info(
                    "  Maximum processing time: %.2f seconds",
                    summary.max_processing_time,
                )

                if summary.avg_processing_time > LONG_PROCESSING_TIME:
                    logger.info(
                        "  Performance note: High average processing time detected"
                    )
                elif summary.avg_processing_time < VERY_FAST_PROCESSING_TIME:
                    logger.info("  Performance note: Very fast average processing time")

            if summary.avg_memory_usage > 0:
                logger.info(
                    "  Average memory usage: %.2f MB",
                    summary.avg_memory_usage,
                )
                logger.info(
                    "  Total memory usage: %.2f MB",
                    summary.total_memory_usage,
                )

                if summary.avg_memory_usage > HIGH_MEMORY_USAGE:
                    logger.info("  Memory note: High memory usage detected")
                elif summary.avg_memory_usage < LOW_MEMORY_USAGE:
                    logger.info("  Memory note: Very low memory usage")

            if summary.total_time > 0:
                throughput = summary.processed_files / summary.total_time
                logger.info(
                    "  Processing throughput: %.2f files/second",
                    throughput,
                )

        except (ZeroDivisionError, ArithmeticError):
            logger.exception("Error calculating summary statistics")
            logger.info("  Statistics calculation failed due to invalid values")

    def _log_analysis(self, summary: ProcessingSummary) -> None:
        logger.info("Analysis and Recommendations:")
        self._log_error_analysis(summary)
        self._log_timeout_and_coverage(summary)
        self._log_success_analysis(summary)

    def _log_error_analysis(self, summary: ProcessingSummary) -> None:
        if summary.errors <= 0:
            return
        error_percentage = (summary.errors / summary.total_files) * 100
        logger.info("  - Error Analysis (%.1f%% error rate):", error_percentage)

        if summary.parsing_errors > 0:
            parsing_pct = (summary.parsing_errors / summary.errors) * 100
            logger.info(
                "    * Parsing errors: %d (%.1f%% of errors)",
                summary.parsing_errors,
                parsing_pct,
            )
            logger.info("      - Check SMT-LIB file format compatibility")
            logger.info("      - Verify file encoding and syntax")
            logger.info("      - Look for unsupported operators or constructs")

        if summary.solver_errors > 0:
            solver_pct = (summary.solver_errors / summary.errors) * 100
            logger.info(
                "    * Solver errors: %d (%.1f%% of errors)",
                summary.solver_errors,
                solver_pct,
            )
            logger.info("      - Check solver configuration and capabilities")
            logger.info("      - Consider memory and resource constraints")
            logger.info("      - Review solver-specific limitations")

        if summary.validation_errors > 0:
            validation_pct = (summary.validation_errors / summary.errors) * 100
            logger.info(
                "    * Validation errors: %d (%.1f%% of errors)",
                summary.validation_errors,
                validation_pct,
            )
            logger.info("      - Check file permissions and accessibility")
            logger.info("      - Verify file paths and existence")
            logger.info("      - Ensure files are not corrupted")

        if summary.general_errors > 0:
            general_pct = (summary.general_errors / summary.errors) * 100
            logger.info(
                "    * General errors: %d (%.1f%% of errors)",
                summary.general_errors,
                general_pct,
            )
            logger.info("      - Review system resources and stability")
            logger.info("      - Check for unexpected runtime conditions")
            logger.info("      - Consider enabling debug logging for details")

        if error_percentage > CRITICAL_ERROR_RATE:
            logger.info("  - CRITICAL: Very high error rate (>50%)")
            logger.info("    * Review system configuration and file quality")
        elif error_percentage > WARNING_ERROR_RATE:
            logger.info("  - WARNING: High error rate (>20%)")
            logger.info("    * Consider filtering problematic files")
        else:
            logger.info("  - Acceptable error rate - monitor for patterns")

    def _log_timeout_and_coverage(self, summary: ProcessingSummary) -> None:
        if summary.timeouts > 0:
            timeout_percentage = (summary.timeouts / summary.total_files) * 100
            if timeout_percentage > HIGH_TIMEOUT_RATE:
                logger.info("  - High timeout rate detected. Consider:")
                logger.info("    * Increasing timeout values")
                logger.info("    * Using more powerful hardware")
                logger.info("    * Filtering out complex benchmark files")
            else:
                logger.info(
                    "  - Timeout rate: %.1f%% - within acceptable range",
                    timeout_percentage,
                )

        if summary.total_files > summary.processed_files:
            skipped = summary.total_files - summary.processed_files
            skip_percentage = (skipped / summary.total_files) * 100
            logger.info(
                "  - %d files (%.1f%%) were skipped",
                skipped,
                skip_percentage,
            )
            logger.info("    * Check file validation logs for reasons")
            logger.info("    * Verify file accessibility and permissions")

    def _log_success_analysis(self, summary: ProcessingSummary) -> None:
        if summary.successful <= 0:
            return
        success_percentage = (summary.successful / summary.total_files) * 100
        if success_percentage > EXCELLENT_SUCCESS_RATE:
            logger.info("  - Excellent success rate (%.1f%%)", success_percentage)
        elif success_percentage > GOOD_SUCCESS_RATE:
            logger.info("  - Good success rate (%.1f%%)", success_percentage)
        else:
            logger.info(
                "  - Low success rate (%.1f%%) - investigate issues",
                success_percentage,
            )
