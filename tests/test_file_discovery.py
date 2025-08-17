"""Tests for file discovery utilities."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from performance_test.file_discovery import discover_smt2_files, validate_file


class TestDiscoverSmt2Files:
    """Tests for discover_smt2_files function."""

    def test_discover_files_in_valid_directory(self):
        """Test discovering files in a directory with SMT2 files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create some test SMT2 files
            (temp_path / "test1.smt2").write_text("(set-info :status sat)")
            (temp_path / "test2.smt2").write_text("(set-info :status unsat)")
            (temp_path / "other.txt").write_text("not an smt2 file")

            files = discover_smt2_files(temp_path)

            assert len(files) == 2
            assert all(f.suffix == ".smt2" for f in files)
            assert all(f.is_file() for f in files)
            # Check files are sorted
            assert files[0].name == "test1.smt2"
            assert files[1].name == "test2.smt2"

    def test_discover_files_with_custom_pattern(self):
        """Test discovering files with a custom glob pattern."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test files
            (temp_path / "ARI001=1.smt2").write_text("(set-info :status sat)")
            (temp_path / "NUM001=1.smt2").write_text("(set-info :status unsat)")
            (temp_path / "OTHER001=1.smt2").write_text("(set-info :status sat)")

            # Test with pattern that matches only ARI files
            files = discover_smt2_files(temp_path, "ARI*.smt2")

            assert len(files) == 1
            assert files[0].name == "ARI001=1.smt2"

    def test_discover_files_empty_directory(self):
        """Test discovering files in an empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            files = discover_smt2_files(temp_path)

            assert files == []

    def test_discover_files_no_matching_files(self):
        """Test discovering files when no files match the pattern."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create non-matching files
            (temp_path / "test.txt").write_text("not an smt2 file")
            (temp_path / "other.log").write_text("log file")

            files = discover_smt2_files(temp_path)

            assert files == []

    def test_discover_files_nonexistent_directory(self):
        """Test discovering files in a non-existent directory."""
        nonexistent_path = Path("/nonexistent/directory")

        with pytest.raises(
            FileNotFoundError, match="Benchmark directory does not exist"
        ):
            discover_smt2_files(nonexistent_path)

    def test_discover_files_path_is_file(self):
        """Test discovering files when path points to a file instead of directory."""
        with tempfile.NamedTemporaryFile() as temp_file:
            file_path = Path(temp_file.name)

            with pytest.raises(
                NotADirectoryError, match="Path exists but is not a directory"
            ):
                discover_smt2_files(file_path)

    @patch("performance_test.file_discovery.logger")
    def test_discover_files_logs_info(self, mock_logger):
        """Test that the function logs appropriate info messages."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "test.smt2").write_text("(set-info :status sat)")

            discover_smt2_files(temp_path)

            # The function now logs multiple info messages, so check that it was called
            assert mock_logger.info.call_count >= 1
            # Check that one of the calls contains the file discovery completion message
            info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
            assert any(
                "File discovery completed: 1 SMT2 files found" in call
                for call in info_calls
            )

    @patch("performance_test.file_discovery.logger")
    def test_discover_files_logs_warning_when_empty(self, mock_logger):
        """Test that the function logs warning when no files found."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            discover_smt2_files(temp_path)

            mock_logger.warning.assert_called_once()
            assert "No files matching pattern" in mock_logger.warning.call_args[0][0]


class TestValidateFile:
    """Tests for validate_file function."""

    def test_validate_existing_readable_file(self):
        """Test validating an existing, readable file."""
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".smt2"
        ) as temp_file:
            temp_file.write("(set-info :status sat)")
            temp_file.flush()
            file_path = Path(temp_file.name)

        try:
            result = validate_file(file_path)
            assert result is True
        finally:
            file_path.unlink()  # Clean up

    def test_validate_nonexistent_file(self):
        """Test validating a non-existent file."""
        nonexistent_path = Path("/nonexistent/file.smt2")

        result = validate_file(nonexistent_path)

        assert result is False

    def test_validate_directory_instead_of_file(self):
        """Test validating a directory path instead of a file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            dir_path = Path(temp_dir)

            result = validate_file(dir_path)

            assert result is False

    @patch("performance_test.file_discovery.logger")
    def test_validate_file_logs_warnings_and_errors(self, mock_logger):
        """Test that validation logs appropriate messages."""
        # Test non-existent file
        nonexistent_path = Path("/nonexistent/file.smt2")
        validate_file(nonexistent_path)
        mock_logger.warning.assert_called()
        assert (
            "File validation failed - file does not exist"
            in mock_logger.warning.call_args[0][0]
        )

        # Test directory instead of file
        with tempfile.TemporaryDirectory() as temp_dir:
            dir_path = Path(temp_dir)
            validate_file(dir_path)
            # Should have been called twice now
            assert mock_logger.warning.call_count == 2
            assert (
                "File validation failed - path is not a regular file"
                in mock_logger.warning.call_args[0][0]
            )

    def test_validate_file_handles_unicode_decode_error(self):
        """Test that validation handles files with encoding issues gracefully."""
        with tempfile.NamedTemporaryFile(
            mode="wb", delete=False, suffix=".smt2"
        ) as temp_file:
            # Write some binary data that will cause UnicodeDecodeError
            temp_file.write(b"\xff\xfe\x00\x00invalid utf-8")
            file_path = Path(temp_file.name)

        try:
            result = validate_file(file_path)
            # Should still return True as SMT2 files might have different encodings
            assert result is True
        finally:
            file_path.unlink()  # Clean up

    def test_validate_empty_file(self):
        """Test validating an empty file."""
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".smt2"
        ) as temp_file:
            # Create empty file
            temp_file.write("")
            file_path = Path(temp_file.name)

        try:
            result = validate_file(file_path)
            # Empty files should still be considered valid
            assert result is True
        finally:
            file_path.unlink()  # Clean up

    @patch("pathlib.Path.open")
    def test_validate_file_permission_error(self, mock_open):
        """Test validation when file cannot be opened due to permissions."""
        mock_open.side_effect = PermissionError("Permission denied")

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".smt2"
        ) as temp_file:
            temp_file.write("(set-info :status sat)")
            file_path = Path(temp_file.name)

        try:
            result = validate_file(file_path)
            assert result is False
        finally:
            file_path.unlink()  # Clean up

    @patch("pathlib.Path.stat")
    def test_validate_file_stat_error(self, mock_stat):
        """Test validation when file stats cannot be retrieved."""
        mock_stat.side_effect = OSError("Cannot get file stats")

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".smt2"
        ) as temp_file:
            temp_file.write("(set-info :status sat)")
            file_path = Path(temp_file.name)

        try:
            result = validate_file(file_path)
            assert result is False
        finally:
            file_path.unlink()  # Clean up

    @patch("pathlib.Path.glob")
    def test_discover_files_glob_error(self, mock_glob):
        """Test file discovery when glob operation fails."""
        mock_glob.side_effect = OSError("Glob operation failed")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            with pytest.raises(OSError, match="Error during file pattern matching"):
                discover_smt2_files(temp_path)

    @patch("pathlib.Path.glob")
    def test_discover_files_invalid_pattern(self, mock_glob):
        """Test file discovery with invalid glob pattern."""
        mock_glob.side_effect = ValueError("Invalid pattern")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            with pytest.raises(ValueError, match="Invalid pattern"):
                discover_smt2_files(temp_path, "[invalid")

    @patch("pathlib.Path.iterdir")
    def test_discover_files_permission_error(self, mock_iterdir):
        """Test file discovery when directory cannot be accessed."""
        mock_iterdir.side_effect = PermissionError("Permission denied")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            with pytest.raises(
                PermissionError, match="Permission denied: Cannot access directory"
            ):
                discover_smt2_files(temp_path)

    def test_discover_files_with_subdirectories(self):
        """Test that subdirectories are properly filtered out."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create files and subdirectories
            (temp_path / "test1.smt2").write_text("(set-info :status sat)")
            (temp_path / "test2.smt2").write_text("(set-info :status unsat)")
            (temp_path / "subdir").mkdir()
            (temp_path / "subdir" / "nested.smt2").write_text("(set-info :status sat)")

            files = discover_smt2_files(temp_path)

            # Should only find files in the root directory, not subdirectories
            assert len(files) == 2
            assert all(f.parent == temp_path for f in files)
            assert all(f.suffix == ".smt2" for f in files)

    def test_discover_files_with_broken_symlinks(self):
        """Test file discovery with broken symbolic links."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a regular file
            (temp_path / "test1.smt2").write_text("(set-info :status sat)")

            # Create a broken symlink (pointing to non-existent file)
            broken_link = temp_path / "broken.smt2"
            try:
                broken_link.symlink_to("nonexistent.smt2")
            except OSError:
                # Skip this test if symlinks are not supported
                pytest.skip("Symbolic links not supported on this system")

            files = discover_smt2_files(temp_path)

            # Should only find the regular file, broken symlink should be filtered out
            assert len(files) == 1
            assert files[0].name == "test1.smt2"
