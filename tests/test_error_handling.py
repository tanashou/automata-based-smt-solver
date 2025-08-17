"""Tests for error handling scenarios across the benchmark processing system."""

import io
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from performance_test.file_discovery import discover_smt2_files, validate_file
from performance_test.progress_reporter import ProgressReporter


class TestIntegratedErrorHandling:
    """Test error handling scenarios that involve multiple components."""

    def test_complete_workflow_with_mixed_file_conditions(self):
        """Test complete workflow with various file conditions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create various types of files and conditions
            (temp_path / "valid.smt2").write_text("(set-info :status sat)")
            (temp_path / "empty.smt2").write_text("")
            (temp_path / "subdir").mkdir()
            (temp_path / "not_smt2.txt").write_text("not an smt2 file")

            # Create a file with permission issues (if possible)
            restricted_file = temp_path / "restricted.smt2"
            restricted_file.write_text("(set-info :status unsat)")

            # Discover files
            files = discover_smt2_files(temp_path)

            # Should find valid and empty SMT2 files
            assert len(files) >= 2

            # Validate each file
            reporter = ProgressReporter()
            reporter.report_start(len(files))

            valid_files = []
            for i, file_path in enumerate(files, 1):
                if validate_file(file_path):
                    valid_files.append(file_path)
                    reporter.report_file_result(
                        file_path.name, "sat", "sat", 1.0, "10.0"
                    )
                else:
                    reporter.report_file_result(
                        file_path.name, "error", "sat", 0.1, "N/A", "validation"
                    )
                reporter.report_progress(i, file_path.name)

            summary = reporter.report_summary()

            # Should have processed all discovered files
            assert summary.total_files == len(files)
            assert summary.processed_files == len(files)

    def test_file_discovery_with_concurrent_file_deletion(self):
        """Test file discovery when files are deleted during processing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test files
            file1 = temp_path / "test1.smt2"
            file2 = temp_path / "test2.smt2"
            file1.write_text("(set-info :status sat)")
            file2.write_text("(set-info :status unsat)")

            # Discover files
            files = discover_smt2_files(temp_path)
            assert len(files) == 2

            # Delete one file after discovery
            file1.unlink()

            # Validate remaining files
            valid_count = 0
            for file_path in files:
                if validate_file(file_path):
                    valid_count += 1

            # Should only validate the remaining file
            assert valid_count == 1

    def test_error_recovery_in_batch_processing(self):
        """Test that processing continues after individual file errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create mix of valid and problematic files
            (temp_path / "valid1.smt2").write_text("(set-info :status sat)")
            (temp_path / "valid2.smt2").write_text("(set-info :status unsat)")
            (temp_path / "valid3.smt2").write_text("(set-info :status unknown)")

            files = discover_smt2_files(temp_path)
            reporter = ProgressReporter()
            reporter.report_start(len(files))

            # Simulate processing with some errors
            for i, file_path in enumerate(files, 1):
                try:
                    if validate_file(file_path):
                        # Simulate different outcomes
                        if "valid1" in file_path.name:
                            reporter.report_file_result(
                                file_path.name, "sat", "sat", 1.0, "10.0"
                            )
                        elif "valid2" in file_path.name:
                            reporter.report_file_result(
                                file_path.name, "timeout", "unsat", 60.0, "N/A"
                            )
                        else:
                            reporter.report_file_result(
                                file_path.name, "error", "unknown", 0.5, "N/A", "solver"
                            )
                    else:
                        reporter.report_file_result(
                            file_path.name, "error", "unknown", 0.1, "N/A", "validation"
                        )
                except (OSError, ValueError, RuntimeError):
                    # Even if individual file processing fails, continue
                    reporter.report_file_result(
                        file_path.name, "error", "unknown", 0.0, "N/A", "general"
                    )

                reporter.report_progress(i, file_path.name)

            summary = reporter.report_summary()

            # Should have attempted to process all files
            assert summary.total_files == len(files)
            assert summary.processed_files == len(files)

    @patch("performance_test.file_discovery.logger")
    def test_logging_during_error_conditions(self, mock_logger):
        """Test that appropriate logging occurs during error conditions."""
        # Test with non-existent directory
        nonexistent_path = Path("/nonexistent/directory")

        with pytest.raises(FileNotFoundError):
            discover_smt2_files(nonexistent_path)

        # Should have logged error messages
        mock_logger.error.assert_called()
        error_calls = [call[0][0] for call in mock_logger.error.call_args_list]
        assert any("Benchmark directory does not exist" in call for call in error_calls)

    def test_memory_and_resource_error_handling(self):
        """Test handling of memory and resource-related errors."""
        reporter = ProgressReporter()
        reporter.report_start(1)

        # Test with various memory usage formats
        memory_values = ["N/A", "invalid", "1000.5", "", None]

        for i, memory_val in enumerate(memory_values):
            try:
                reporter.report_file_result(
                    f"test{i}.smt2", "sat", "sat", 1.0, memory_val
                )
            except (TypeError, ValueError) as e:
                # Should handle invalid memory values gracefully
                pytest.fail(
                    f"Should not raise exception for memory value {memory_val}: {e}"
                )

        summary = reporter.report_summary()
        # Should complete successfully despite invalid memory values
        assert summary.successful >= 0

    def test_unicode_and_encoding_error_handling(self):
        """Test handling of various encoding issues."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create files with different encodings
            utf8_file = temp_path / "utf8.smt2"
            utf8_file.write_text("(set-info :status sat)", encoding="utf-8")

            latin1_file = temp_path / "latin1.smt2"
            latin1_file.write_text("(set-info :status unsat)", encoding="latin-1")

            # Create binary file that will cause encoding issues
            binary_file = temp_path / "binary.smt2"
            binary_file.write_bytes(b"\xff\xfe\x00\x00binary data")

            files = discover_smt2_files(temp_path)

            # All files should be discovered
            assert len(files) == 3

            # Validation should handle encoding issues gracefully
            valid_count = 0
            for file_path in files:
                if validate_file(file_path):
                    valid_count += 1

            # At least the UTF-8 and Latin-1 files should be valid
            assert valid_count >= 2

    def test_concurrent_access_error_handling(self):
        """Test handling of concurrent access issues."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_file = temp_path / "test.smt2"
            test_file.write_text("(set-info :status sat)")

            # Simulate concurrent access by mocking file operations
            with patch("pathlib.Path.open") as mock_open:
                # First call succeeds, second fails with permission error
                mock_open.side_effect = [
                    io.StringIO("content"),
                    PermissionError("File is locked"),
                ]

                # First validation should succeed
                result1 = validate_file(test_file)
                assert result1 is True

                # Second validation should fail gracefully
                result2 = validate_file(test_file)

                assert result2 is False  # Should handle permission error

    def test_system_resource_exhaustion_simulation(self):
        """Test handling of system resource exhaustion."""
        reporter = ProgressReporter()

        # Test with extreme values that might cause issues
        reporter.report_start(1000000)  # Very large number

        # Should handle large numbers gracefully
        assert reporter._total_files == 1000000

        # Test with very long filenames
        long_filename = "a" * 1000 + ".smt2"
        reporter.report_file_result(long_filename, "sat", "sat", 1.0, "10.0")

        summary = reporter.report_summary()
        # Should complete without errors
        assert summary.total_files == 1000000

    def test_edge_case_glob_patterns(self):
        """Test file discovery with edge case glob patterns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create files with special characters
            (temp_path / "test[1].smt2").write_text("(set-info :status sat)")
            (temp_path / "test(2).smt2").write_text("(set-info :status unsat)")
            (temp_path / "test{3}.smt2").write_text("(set-info :status unknown)")

            # Test with various patterns
            patterns = ["*.smt2", "*[1]*.smt2", "*(*).smt2", "*{*}.smt2"]

            for pattern in patterns:
                try:
                    files = discover_smt2_files(temp_path, pattern)
                    # Should not raise exceptions
                    assert isinstance(files, list)
                except ValueError:
                    # Some patterns might be invalid, which is acceptable
                    pass

    def test_cleanup_after_errors(self):
        """Test that resources are properly cleaned up after errors."""
        reporter = ProgressReporter()

        # Start processing
        reporter.report_start(3)

        # Simulate processing with errors
        reporter.report_file_result("file1.smt2", "sat", "sat", 1.0, "10.0")
        reporter.report_file_result("file2.smt2", "error", "sat", 0.1, "N/A", "parsing")

        # Even with errors, should be able to generate summary
        summary = reporter.report_summary()

        assert summary.successful == 1
        assert summary.errors == 1
        assert summary.total_files == 3

        # Should be able to start a new session
        reporter.report_start(1)
        assert reporter._total_files == 1
        assert reporter._successful == 0  # Should reset counters
