"""Tests for progress reporting functionality."""

import logging
from unittest.mock import patch

from performance_test.progress_reporter import ProcessingSummary, ProgressReporter


class TestProgressReporter:
    """Test cases for ProgressReporter class."""

    def test_initialization(self):
        """Test that ProgressReporter initializes correctly."""
        reporter = ProgressReporter()
        assert reporter._start_time is None
        assert reporter._total_files == 0
        assert reporter._processed_files == 0
        assert reporter._successful == 0
        assert reporter._errors == 0
        assert reporter._timeouts == 0

    def test_report_start(self, caplog):
        """Test report_start method."""
        reporter = ProgressReporter()

        with caplog.at_level(logging.INFO):
            reporter.report_start(5)

        assert reporter._total_files == 5
        assert reporter._start_time is not None
        assert "Starting benchmark processing: 5 files to process" in caplog.text
        assert "Filename" in caplog.text  # Check header is logged

    def test_report_progress(self, caplog):
        """Test report_progress method."""
        reporter = ProgressReporter()
        reporter.report_start(3)

        with caplog.at_level(logging.INFO):
            reporter.report_progress(2, "test_file.smt2")

        assert reporter._processed_files == 2
        assert "Processing file 2/3" in caplog.text
        assert "test_file.smt2" in caplog.text

    def test_report_file_result_successful(self, caplog):
        """Test report_file_result with successful result."""
        reporter = ProgressReporter()
        reporter.report_start(1)

        with caplog.at_level(logging.INFO):
            reporter.report_file_result("test.smt2", "sat", "sat", 1.234, "10.5")

        assert reporter._successful == 1
        assert reporter._errors == 0
        assert reporter._timeouts == 0
        assert "test.smt2" in caplog.text
        assert "sat" in caplog.text

    def test_report_file_result_timeout(self, caplog):
        """Test report_file_result with timeout result."""
        reporter = ProgressReporter()
        reporter.report_start(1)

        with caplog.at_level(logging.INFO):
            reporter.report_file_result("test.smt2", "timeout", "sat", 60.0, "N/A")

        assert reporter._successful == 0
        assert reporter._errors == 0
        assert reporter._timeouts == 1
        assert "timeout" in caplog.text

    def test_report_file_result_error(self, caplog):
        """Test report_file_result with error result."""
        reporter = ProgressReporter()
        reporter.report_start(1)

        with caplog.at_level(logging.INFO):
            reporter.report_file_result("test.smt2", "error", "sat", 0.5, "N/A")

        assert reporter._successful == 0
        assert reporter._errors == 1
        assert reporter._timeouts == 0
        assert "error" in caplog.text

    def test_report_summary(self, caplog):
        """Test report_summary method."""
        reporter = ProgressReporter()
        reporter.report_start(3)

        # Simulate processing some files
        reporter.report_file_result("file1.smt2", "sat", "sat", 1.0, "10.0")
        reporter.report_file_result("file2.smt2", "timeout", "unsat", 60.0, "N/A")
        reporter.report_file_result("file3.smt2", "error", "sat", 0.1, "N/A")

        with caplog.at_level(logging.INFO):
            summary = reporter.report_summary()

        assert isinstance(summary, ProcessingSummary)
        assert summary.total_files == 3
        assert summary.successful == 1
        assert summary.errors == 1
        assert summary.timeouts == 1
        assert summary.total_time > 0

        # Check summary is logged with new enhanced format
        assert "FINAL PROCESSING SUMMARY:" in caplog.text
        assert "Total files discovered: 3" in caplog.text
        assert "Successful results: 1" in caplog.text
        assert "Errors encountered: 1" in caplog.text
        assert "Timeouts occurred: 1" in caplog.text
        assert "Success rate:" in caplog.text

    def test_report_summary_no_start_time(self):
        """Test report_summary when start time was never set."""
        reporter = ProgressReporter()
        # Don't call report_start

        summary = reporter.report_summary()

        assert summary.total_time == 0.0
        assert summary.total_files == 0

    @patch("time.time")
    def test_timing_calculation(self, mock_time):
        """Test that timing is calculated correctly."""
        # Mock time.time to return predictable values
        mock_time.side_effect = [100.0, 105.0]  # 5 second difference

        reporter = ProgressReporter()
        reporter.report_start(1)

        summary = reporter.report_summary()

        assert summary.total_time == 5.0

    def test_success_rate_calculation(self, caplog):
        """Test success rate calculation in summary."""
        reporter = ProgressReporter()
        reporter.report_start(4)

        # 3 successful, 1 error = 75% success rate
        reporter.report_file_result("file1.smt2", "sat", "sat", 1.0, "10.0")
        reporter.report_file_result("file2.smt2", "unsat", "unsat", 1.0, "10.0")
        reporter.report_file_result("file3.smt2", "sat", "sat", 1.0, "10.0")
        reporter.report_file_result("file4.smt2", "error", "sat", 0.1, "N/A")

        with caplog.at_level(logging.INFO):
            summary = reporter.report_summary()

        assert "Success rate: 75.0%" in caplog.text
        assert summary.successful == 3
        assert summary.total_files == 4

    def test_report_file_result_with_error_types(self):
        """Test reporting file results with different error types."""
        reporter = ProgressReporter()
        reporter.report_start(4)

        # Test different error types
        reporter.report_file_result("file1.smt2", "error", "sat", 0.1, "N/A", "parsing")
        reporter.report_file_result("file2.smt2", "error", "sat", 0.2, "N/A", "solver")
        reporter.report_file_result(
            "file3.smt2", "error", "sat", 0.3, "N/A", "validation"
        )
        reporter.report_file_result("file4.smt2", "error", "sat", 0.4, "N/A", "general")

        summary = reporter.report_summary()

        assert summary.errors == 4
        assert summary.parsing_errors == 1
        assert summary.solver_errors == 1
        assert summary.validation_errors == 1
        assert summary.general_errors == 1

    def test_report_file_result_invalid_inputs(self, caplog):
        """Test reporting file results with invalid inputs."""
        reporter = ProgressReporter()
        reporter.report_start(1)

        with caplog.at_level(logging.WARNING):
            # Test with invalid filename
            reporter.report_file_result("", "sat", "sat", 1.0, "10.0")

            # Test with invalid result type
            reporter.report_file_result("test.smt2", 123, "sat", 1.0, "10.0")  # pyright: ignore[reportArgumentType]

            # Test with invalid execution time
            reporter.report_file_result("test.smt2", "sat", "sat", -1.0, "10.0")

        # Should handle invalid inputs gracefully
        assert "Invalid filename provided" in caplog.text
        assert "Invalid result type provided" in caplog.text
        assert "Invalid execution_time provided" in caplog.text

    def test_report_file_result_result_mismatch(self, caplog):
        """Test reporting when result doesn't match expected status."""
        reporter = ProgressReporter()
        reporter.report_start(1)

        with caplog.at_level(logging.WARNING):
            reporter.report_file_result("test.smt2", "sat", "unsat", 1.0, "10.0")

        summary = reporter.report_summary()

        assert summary.result_mismatches == 1
        assert (
            "Result mismatch for test.smt2: got 'sat', expected 'unsat'" in caplog.text
        )

    def test_report_file_result_unexpected_result_type(self, caplog):
        """Test reporting with unexpected result type."""
        reporter = ProgressReporter()
        reporter.report_start(1)

        with caplog.at_level(logging.WARNING):
            reporter.report_file_result(
                "test.smt2", "invalid_result", "sat", 1.0, "10.0"
            )

        summary = reporter.report_summary()

        assert summary.errors == 1
        assert "Unexpected result type 'invalid_result'" in caplog.text

    def test_report_progress_with_eta_calculation(self, caplog):
        """Test progress reporting with ETA calculation."""
        reporter = ProgressReporter()
        reporter.report_start(10)

        with caplog.at_level(logging.INFO):
            # First file - should show "calculating..."
            reporter.report_progress(1, "file1.smt2")
            assert "ETA: calculating..." in caplog.text

            # Simulate some time passing and report second file
            with patch("time.time") as mock_time:
                mock_time.side_effect = [100.0, 102.0]  # 2 seconds elapsed
                reporter._start_time = 100.0
                reporter.report_progress(2, "file2.smt2")
                # Should calculate ETA based on processing speed

    def test_enhanced_summary_statistics(self):
        """Test enhanced summary statistics calculation."""
        reporter = ProgressReporter()
        reporter.report_start(5)

        # Add various results with different processing times
        reporter.report_file_result("fast.smt2", "sat", "sat", 0.1, "5.0")
        reporter.report_file_result("slow.smt2", "unsat", "unsat", 10.0, "50.0")
        reporter.report_file_result("medium.smt2", "unknown", "unknown", 2.0, "20.0")
        reporter.report_file_result("timeout.smt2", "timeout", "sat", 60.0, "N/A")
        reporter.report_file_result("error.smt2", "error", "sat", 0.5, "N/A", "parsing")

        summary = reporter.report_summary()

        # Check enhanced statistics
        assert summary.min_processing_time == 0.1
        assert summary.max_processing_time == 10.0
        assert (
            summary.avg_processing_time == (0.1 + 10.0 + 2.0) / 3
        )  # Only successful results
        assert summary.sat_results == 1
        assert summary.unsat_results == 1
        assert summary.unknown_results == 1
        assert summary.fastest_file == "fast.smt2"
        assert summary.slowest_file == "slow.smt2"
        assert summary.most_problematic_error_type == "parsing"

    def test_report_start_with_config_info(self, caplog):
        """Test report_start with configuration information."""
        reporter = ProgressReporter()
        config = {"solver": "Z3", "timeout": 60, "pattern": "*.smt2"}

        with caplog.at_level(logging.INFO):
            reporter.report_start(5, config)

        assert "CONFIGURATION:" in caplog.text
        assert "solver: Z3" in caplog.text
        assert "timeout: 60" in caplog.text
        assert "pattern: *.smt2" in caplog.text

    def test_negative_time_handling(self):
        """Test handling of negative time calculations."""
        reporter = ProgressReporter()

        # Manually set start time and then mock time.time for summary
        reporter._start_time = 100.0

        with patch("time.time", return_value=95.0):  # Time goes backwards
            summary = reporter.report_summary()

        # Should handle negative time gracefully
        assert summary.total_time == 0.0
