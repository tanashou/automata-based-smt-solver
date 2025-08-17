"""Integration tests for dynamic benchmark file processing functionality.

This module tests the complete end-to-end functionality of the benchmark processing
system, including file discovery, argument parsing, progress reporting, and solver
integration with real benchmark files.
"""

import importlib
import os
import sys
import tempfile
import time
from contextlib import suppress
from pathlib import Path

import pytest

from performance_test.file_discovery import discover_smt2_files, validate_file
from performance_test.progress_reporter import ProgressReporter


class TestBenchmarkDirectoryStructure:
    """Test integration with actual benchmark directory structure."""

    def test_discover_files_in_tptp_directory(self):
        """Test file discovery with the actual tptp benchmark directory."""
        tptp_dir = Path("benchmarks/LIA/tptp")

        if not tptp_dir.exists():
            pytest.skip("TPTP benchmark directory not found")

        files = discover_smt2_files(tptp_dir)

        # Should find SMT2 files in the tptp directory
        assert len(files) > 0, "Should find SMT2 files in tptp directory"
        assert all(f.suffix == ".smt2" for f in files), (
            "All files should have .smt2 extension"
        )
        assert all(f.parent == tptp_dir for f in files), (
            "All files should be in tptp directory"
        )

        # Check for expected file patterns (ARI and NUM files)
        file_names = [f.name for f in files]
        ari_files = [name for name in file_names if name.startswith("ARI")]
        num_files = [name for name in file_names if name.startswith("NUM")]

        assert len(ari_files) > 0, "Should find ARI benchmark files"
        assert len(num_files) > 0, "Should find NUM benchmark files"

    def test_discover_files_in_psyco_directory(self):
        """Test file discovery with the psyco benchmark directory."""
        psyco_dir = Path("benchmarks/LIA/psyco")

        if not psyco_dir.exists():
            pytest.skip("Psyco benchmark directory not found")

        files = discover_smt2_files(psyco_dir)

        # Should find many SMT2 files in the psyco directory
        assert len(files) > 50, "Should find many SMT2 files in psyco directory"
        assert all(f.suffix == ".smt2" for f in files), (
            "All files should have .smt2 extension"
        )

        # Check for expected numeric naming pattern
        file_names = [f.name for f in files]
        numeric_files = [
            name for name in file_names if name.replace(".smt2", "").isdigit()
        ]

        assert len(numeric_files) > 0, "Should find numerifiles"

    def test_discover_files_in_ultimate_automizer_directory(self):
        """Test file discovery with the UltimateAutomizer benchmark directory."""
        ultimate_dir = Path("benchmarks/LIA/UltimateAutomizer")

        if not ultimate_dir.exists():
            pytest.skip("UltimateAutomizer benchmark directory not found")

        files = discover_smt2_files(ultimate_dir)

        # Should find SMT2 files in the UltimateAutomizer directory
        assert len(files) > 0, "Should find SMT2 files in UltimateAutomizer directory"
        assert all(f.suffix == ".smt2" for f in files), (
            "All files should have .smt2 extension"
        )

        # Check for expected file patterns
        file_names = [f.name for f in files]
        nested_files = [name for name in file_names if "nested" in name]
        primes_files = [name for name in file_names if "Primes" in name]

        assert len(nested_files) > 0 or len(primes_files) > 0, (
            "Should find expected benchmark files"
        )

    def test_validate_actual_benchmark_files(self):
        """Test file validation with actual benchmark files."""
        tptp_dir = Path("benchmarks/LIA/tptp")

        if not tptp_dir.exists():
            pytest.skip("TPTP benchmark directory not found")

        files = discover_smt2_files(tptp_dir)

        if not files:
            pytest.skip("No files found in tptp directory")

        # Test validation on first few files
        for file_path in files[:5]:
            assert validate_file(file_path), f"File should be valid: {file_path.name}"


class TestFilePatternFiltering:
    """Test various file patterns and filters."""

    def test_ari_pattern_filtering(self):
        """Test filtering for ARI files only."""
        tptp_dir = Path("benchmarks/LIA/tptp")

        if not tptp_dir.exists():
            pytest.skip("TPTP benchmark directory not found")

        # Test ARI pattern
        ari_files = discover_smt2_files(tptp_dir, "ARI*.smt2")

        if ari_files:
            assert all(f.name.startswith("ARI") for f in ari_files), (
                "All files should start with ARI"
            )
            assert all(f.suffix == ".smt2" for f in ari_files), (
                "All files should have .smt2 extension"
            )

    def test_num_pattern_filtering(self):
        """Test filtering for NUM files only."""
        tptp_dir = Path("benchmarks/LIA/tptp")

        if not tptp_dir.exists():
            pytest.skip("TPTP benchmark directory not found")

        # Test NUM pattern
        num_files = discover_smt2_files(tptp_dir, "NUM*.smt2")

        if num_files:
            assert all(f.name.startswith("NUM") for f in num_files), (
                "All files should start with NUM"
            )
            assert all(f.suffix == ".smt2" for f in num_files), (
                "All files should have .smt2 extension"
            )

    def test_specific_file_pattern(self):
        """Test filtering for specific file patterns."""
        psyco_dir = Path("benchmarks/LIA/psyco")

        if not psyco_dir.exists():
            pytest.skip("Psyco benchmark directory not found")

        # Test pattern for files 001-010
        pattern_files = discover_smt2_files(psyco_dir, "00[1-9].smt2")

        if pattern_files:
            # Should find files like 001.smt2, 002.smt2, etc.
            file_names = [f.name for f in pattern_files]
            expected_files = [
                "001.smt2",
                "002.smt2",
                "003.smt2",
                "004.smt2",
                "005.smt2",
                "006.smt2",
                "007.smt2",
                "008.smt2",
                "009.smt2",
            ]

            for expected in expected_files:
                if (psyco_dir / expected).exists():
                    assert expected in file_names, f"Should find {expected}"

    def test_complex_pattern_filtering(self):
        """Test complex glob patterns."""
        ultimate_dir = Path("benchmarks/LIA/UltimateAutomizer")

        if not ultimate_dir.exists():
            pytest.skip("UltimateAutomizer benchmark directory not found")

        # Test pattern for nested files
        nested_files = discover_smt2_files(ultimate_dir, "nested*.smt2")

        if nested_files:
            assert all("nested" in f.name for f in nested_files), (
                "All files should contain 'nested'"
            )
            assert all(f.suffix == ".smt2" for f in nested_files), (
                "All files should have .smt2 extension"
            )

    def test_no_matching_pattern(self):
        """Test pattern that matches no files."""
        tptp_dir = Path("benchmarks/LIA/tptp")

        if not tptp_dir.exists():
            pytest.skip("TPTP benchmark directory not found")

        # Test pattern that should match no files
        no_files = discover_smt2_files(tptp_dir, "NONEXISTENT*.smt2")

        assert no_files == [], "Should find no files with non-matching pattern"


class TestBackwardCompatibility:
    """Test backward compatibility with existing solver functionality."""

    def test_solver_integration_with_discovered_files(self):
        """Test that discovered files work with the existing solver."""
        # Use test fixtures to avoid long-running tests
        fixture_dir = Path("tests/fixtures/benchmarks/QF_LIA/check")

        if not fixture_dir.exists():
            pytest.skip("Test fixture directory not found")

        files = discover_smt2_files(fixture_dir)

        if not files:
            pytest.skip("No test fixture files found")

        # Test that files can be discovered and validated
        for file_path in files[:2]:  # Test first 2 files only
            assert validate_file(file_path), f"File should be valid: {file_path.name}"

            # Verify file can be read (basic compatibility test)
            try:
                content = file_path.read_text(encoding="utf-8")
                assert content.strip(), f"File should have content: {file_path.name}"
                assert "(set-info" in content or "(assert" in content, (
                    f"File should contain SMT-LIB content: {file_path.name}"
                )
            except UnicodeDecodeError:
                # Some files might have different encodings, which is acceptable
                pass

    def test_progress_reporter_integration(self):
        """Test progress reporter integration with file discovery."""
        fixture_dir = Path("tests/fixtures/benchmarks/QF_LIA/check")

        if not fixture_dir.exists():
            pytest.skip("Test fixture directory not found")

        files = discover_smt2_files(fixture_dir)

        if not files:
            pytest.skip("No test fixture files found")

        progress_reporter = ProgressReporter()

        # Test progress reporting workflow
        config_info = {
            "Solver": "Test",
            "Directory": str(fixture_dir),
            "Pattern": "*.smt2",
        }

        progress_reporter.report_start(len(files), config_info)

        for i, file_path in enumerate(files, 1):
            progress_reporter.report_progress(i, file_path.name)
            progress_reporter.report_file_result(
                file_path.name, "sat", "sat", 0.1, "1.0"
            )

        summary = progress_reporter.report_summary()

        assert summary.total_files == len(files)
        assert summary.processed_files == len(files)

    def test_argument_parsing_compatibility(self):
        """Test that argument parsing works with file discovery."""
        # This is tested indirectly through the main scripts, but we can test
        # the integration of parsed arguments with file discovery

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test files
            (temp_path / "test1.smt2").write_text("(set-info :status sat)")
            (temp_path / "test2.smt2").write_text("(set-info :status unsat)")
            (temp_path / "other.txt").write_text("not smt2")

            # Test default pattern
            files = discover_smt2_files(temp_path, "*.smt2")
            assert len(files) == 2

            # Test custom pattern
            files = discover_smt2_files(temp_path, "test1*.smt2")
            assert len(files) == 1
            assert files[0].name == "test1.smt2"


class TestErrorScenarios:
    """Test error scenarios including missing directories and permission issues."""

    def test_missing_directory_handling(self):
        """Test handling of missing benchmark directories."""
        nonexistent_dir = Path("/nonexistent/benchmark/directory")

        with pytest.raises(
            FileNotFoundError, match="Benchmark directory does not exist"
        ):
            discover_smt2_files(nonexistent_dir)

    def test_empty_directory_handling(self):
        """Test handling of empty directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            files = discover_smt2_files(temp_path)
            assert files == []

    def test_directory_with_no_smt2_files(self):
        """Test handling of directories with no SMT2 files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create non-SMT2 files
            (temp_path / "test.txt").write_text("not smt2")
            (temp_path / "other.log").write_text("log file")

            files = discover_smt2_files(temp_path)
            assert files == []

    def test_file_not_directory_error(self):
        """Test error when path points to a file instead of directory."""
        with tempfile.NamedTemporaryFile() as temp_file:
            file_path = Path(temp_file.name)

            with pytest.raises(
                NotADirectoryError, match="Path exists but is not a directory"
            ):
                discover_smt2_files(file_path)

    @pytest.mark.skipif(
        os.name == "nt", reason="Permission tests not reliable on Windows"
    )
    def test_permission_denied_directory(self):
        """Test handling of permission denied errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a subdirectory and remove read permissions
            restricted_dir = temp_path / "restricted"
            restricted_dir.mkdir()
            (restricted_dir / "test.smt2").write_text("(set-info :status sat)")

            try:
                # Remove read permissions
                restricted_dir.chmod(0o000)

                with pytest.raises(PermissionError, match="Permission denied"):
                    discover_smt2_files(restricted_dir)

            finally:
                # Restore permissions for cleanup
                with suppress(OSError):
                    restricted_dir.chmod(0o755)

    def test_invalid_glob_pattern(self):
        """Test handling of invalid glob patterns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Test with a pattern that doesn't cause an error but returns no results
            # Some invalid patterns are handled gracefully by glob
            files = discover_smt2_files(temp_path, "[invalid")
            assert files == [], "Invalid pattern should return no files"

            # Test with a pattern that might cause issues in some systems
            # but handle gracefully if it doesn't raise an error
            try:
                files = discover_smt2_files(temp_path, "**[")
                assert files == [], "Malformed pattern should return no files"
            except (ValueError, OSError):
                # Some systems might raise an error for malformed patterns
                pass

    def test_file_validation_with_unreadable_file(self):
        """Test file validation with unreadable files."""
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".smt2"
        ) as temp_file:
            temp_file.write("(set-info :status sat)")
            file_path = Path(temp_file.name)

        try:
            # File should initially be valid
            assert validate_file(file_path) is True

            # Make file unreadable (skip on Windows where this is unreliable)
            if os.name != "nt":
                file_path.chmod(0o000)
                assert validate_file(file_path) is False

        finally:
            # Restore permissions and clean up
            try:
                file_path.chmod(0o644)
                file_path.unlink()
            except OSError:
                pass

    def test_corrupted_file_handling(self):
        """Test handling of corrupted or invalid SMT2 files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a file with binary content that might cause issues
            corrupted_file = temp_path / "corrupted.smt2"
            corrupted_file.write_bytes(b"\xff\xfe\x00\x00invalid binary content")

            # File discovery should still find it
            files = discover_smt2_files(temp_path)
            assert len(files) == 1
            assert files[0].name == "corrupted.smt2"

            # File validation should handle it gracefully
            result = validate_file(corrupted_file)
            # Should return True as validation only checks existence and readability
            assert result is True


class TestEndToEndIntegration:
    """Test complete end-to-end integration scenarios."""

    def test_complete_workflow_with_test_fixtures(self):
        """Test complete workflow from file discovery to processing.

        Uses test fixtures to simulate end-to-end processing.
        """
        fixture_dir = Path("tests/fixtures/benchmarks/QF_LIA/check")

        if not fixture_dir.exists():
            pytest.skip("Test fixture directory not found")

        # Step 1: File discovery
        files = discover_smt2_files(fixture_dir)

        if not files:
            pytest.skip("No test fixture files found")

        # Step 2: File validation
        valid_files = [fp for fp in files if validate_file(fp)]

        assert len(valid_files) > 0, "Should have at least one valid file"

        # Step 3: Progress reporting simulation
        progress_reporter = ProgressReporter()
        config_info = {
            "Solver": "Integration Test",
            "Directory": str(fixture_dir),
            "Pattern": "*.smt2",
            "Test Mode": "True",
        }

        progress_reporter.report_start(len(valid_files), config_info)

        # Step 4: Simulate processing
        for i, file_path in enumerate(valid_files, 1):
            progress_reporter.report_progress(i, file_path.name)

            # Simulate processing time
            time.sleep(0.01)

            # Simulate result reporting
            progress_reporter.report_file_result(
                file_path.name, "sat", "sat", 0.01, "1.0"
            )

        # Step 5: Final summary
        summary = progress_reporter.report_summary()

        assert summary.total_files == len(valid_files)
        assert summary.processed_files == len(valid_files)
        assert summary.successful == len(valid_files)
        assert summary.errors == 0

    def test_mixed_valid_invalid_files_scenario(self):
        """Test scenario with mix of valid and invalid files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create valid SMT2 files
            (temp_path / "valid1.smt2").write_text(
                "(set-info :status sat)\n(check-sat)"
            )
            (temp_path / "valid2.smt2").write_text(
                "(set-info :status unsat)\n(check-sat)"
            )

            # Create invalid/problematic files
            (temp_path / "empty.smt2").write_text("")
            (temp_path / "binary.smt2").write_bytes(b"\xff\xfe\x00\x00")

            # Create non-SMT2 files (should be filtered out)
            (temp_path / "other.txt").write_text("not smt2")

            # File discovery should find only .smt2 files
            files = discover_smt2_files(temp_path)
            assert len(files) == 4  # valid1, valid2, empty, binary

            # File validation should handle all files
            validation_results = {}
            for file_path in files:
                validation_results[file_path.name] = validate_file(file_path)

            # All files should pass basic validation (existence and readability)
            assert all(validation_results.values()), (
                "All discovered files should pass basic validation"
            )

    @pytest.mark.skipif(
        sys.platform == "win32", reason="Subprocess tests may be unreliable on Windows"
    )
    def test_command_line_integration_dry_run(self):
        """Test command-line integration with a dry run approach."""
        # Test that the main scripts can be imported and have expected functions
        try:
            perf_absmt = importlib.import_module("src.performance_test.perf_absmt")
            perf_z3 = importlib.import_module("src.performance_test.perf_z3")

            # Check that main functions exist
            assert hasattr(perf_absmt, "main"), "perf_absmt should have main function"
            assert hasattr(perf_absmt, "parse_arguments"), (
                "perf_absmt should have parse_arguments function"
            )
            assert hasattr(perf_z3, "main"), "perf_z3 should have main function"
            assert hasattr(perf_z3, "parse_arguments"), (
                "perf_z3 should have parse_arguments function"
            )

        except ImportError as e:
            pytest.skip(f"Could not import performance test modules: {e}")

    def test_large_directory_performance(self):
        """Test performance with a larger number of files."""
        psyco_dir = Path("benchmarks/LIA/psyco")

        if not psyco_dir.exists():
            pytest.skip("Psyco benchmark directory not found")

        start_time = time.time()
        files = discover_smt2_files(psyco_dir)
        discovery_time = time.time() - start_time

        # Should complete discovery reasonably quickly
        assert discovery_time < 5.0, (
            f"File discovery took too long: {discovery_time:.2f}s"
        )

        if files:
            # Test validation performance on subset
            start_time = time.time()
            valid_count = 0
            for file_path in files[:20]:  # Test first 20 files
                if validate_file(file_path):
                    valid_count += 1
            validation_time = time.time() - start_time

            assert validation_time < 2.0, (
                f"File validation took too long: {validation_time:.2f}s"
            )
            assert valid_count > 0, "Should have at least some valid files"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
