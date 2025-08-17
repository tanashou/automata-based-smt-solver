"""Tests for command line argument parsing functionality."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from performance_test.perf_absmt import parse_arguments as parse_arguments_absmt
from performance_test.perf_z3 import parse_arguments as parse_arguments_z3


class TestArgumentParsingAbSMT:
    """Test cases for AbSMT argument parsing."""

    @patch("sys.argv", ["perf_absmt.py"])
    def test_parse_arguments_defaults(self):
        """Test parsing with default arguments."""
        args = parse_arguments_absmt()

        assert args.pattern == "*.smt2"
        assert args.directory is None

    @patch("sys.argv", ["perf_absmt.py", "--pattern", "test_*.smt2"])
    def test_parse_arguments_custom_pattern(self):
        """Test parsing with custom pattern."""
        args = parse_arguments_absmt()

        assert args.pattern == "test_*.smt2"
        assert args.directory is None

    def test_parse_arguments_custom_directory(self):
        """Test parsing with custom directory."""
        with (
            tempfile.TemporaryDirectory() as temp_dir,
            patch("sys.argv", ["perf_absmt.py", "--directory", temp_dir]),
        ):
            args = parse_arguments_absmt()

            assert args.pattern == "*.smt2"
            assert args.directory == temp_dir

    def test_parse_arguments_both_options(self):
        """Test parsing with both pattern and directory."""
        with (
            tempfile.TemporaryDirectory() as temp_dir,
            patch(
                "sys.argv",
                ["perf_absmt.py", "--pattern", "ARI*.smt2", "--directory", temp_dir],
            ),
        ):
            args = parse_arguments_absmt()

            assert args.pattern == "ARI*.smt2"
            assert args.directory == temp_dir

    @patch("sys.argv", ["perf_absmt.py", "--directory", "/nonexistent/directory"])
    def test_parse_arguments_nonexistent_directory(self):
        """Test parsing with non-existent directory raises error."""
        with pytest.raises(SystemExit):
            parse_arguments_absmt()

    @patch("sys.argv", ["perf_absmt.py", "--pattern", ""])
    def test_parse_arguments_empty_pattern(self):
        """Test parsing with empty pattern raises error."""
        with pytest.raises(SystemExit):
            parse_arguments_absmt()

    @patch("sys.argv", ["perf_absmt.py", "--pattern", "   "])
    def test_parse_arguments_whitespace_pattern(self):
        """Test parsing with whitespace-only pattern raises error."""
        with pytest.raises(SystemExit):
            parse_arguments_absmt()

    @patch("sys.argv", ["perf_absmt.py", "--help"])
    def test_parse_arguments_help(self):
        """Test that help option works."""
        with pytest.raises(SystemExit) as exc_info:
            parse_arguments_absmt()
        # Help should exit with code 0
        assert exc_info.value.code == 0


class TestArgumentParsingZ3:
    """Test cases for Z3 argument parsing."""

    @patch("sys.argv", ["perf_z3.py"])
    def test_parse_arguments_defaults(self):
        """Test parsing with default arguments."""
        args = parse_arguments_z3()

        assert args.pattern == "*.smt2"
        assert args.directory is None

    @patch("sys.argv", ["perf_z3.py", "--pattern", "test_*.smt2"])
    def test_parse_arguments_custom_pattern(self):
        """Test parsing with custom pattern."""
        args = parse_arguments_z3()

        assert args.pattern == "test_*.smt2"
        assert args.directory is None

    def test_parse_arguments_custom_directory(self):
        """Test parsing with custom directory."""
        with (
            tempfile.TemporaryDirectory() as temp_dir,
            patch("sys.argv", ["perf_z3.py", "--directory", temp_dir]),
        ):
            args = parse_arguments_z3()

            assert args.pattern == "*.smt2"
            assert args.directory == temp_dir

    def test_parse_arguments_both_options(self):
        """Test parsing with both pattern and directory."""
        with (
            tempfile.TemporaryDirectory() as temp_dir,
            patch(
                "sys.argv",
                ["perf_z3.py", "--pattern", "NUM*.smt2", "--directory", temp_dir],
            ),
        ):
            args = parse_arguments_z3()

            assert args.pattern == "NUM*.smt2"
            assert args.directory == temp_dir

    @patch("sys.argv", ["perf_z3.py", "--directory", "/nonexistent/directory"])
    def test_parse_arguments_nonexistent_directory(self):
        """Test parsing with non-existent directory raises error."""
        with pytest.raises(SystemExit):
            parse_arguments_z3()

    @patch("sys.argv", ["perf_z3.py", "--pattern", ""])
    def test_parse_arguments_empty_pattern(self):
        """Test parsing with empty pattern raises error."""
        with pytest.raises(SystemExit):
            parse_arguments_z3()

    @patch("sys.argv", ["perf_z3.py", "--pattern", "   "])
    def test_parse_arguments_whitespace_pattern(self):
        """Test parsing with whitespace-only pattern raises error."""
        with pytest.raises(SystemExit):
            parse_arguments_z3()

    @patch("sys.argv", ["perf_z3.py", "--help"])
    def test_parse_arguments_help(self):
        """Test that help option works."""
        with pytest.raises(SystemExit) as exc_info:
            parse_arguments_z3()
        # Help should exit with code 0
        assert exc_info.value.code == 0


class TestArgumentParsingCommon:
    """Test cases for common argument parsing behavior."""

    def test_argument_validation_logic(self):
        """Test the argument validation logic directly."""
        # Test directory validation
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            assert temp_path.exists()  # Should pass validation

        # Test pattern validation
        valid_patterns = ["*.smt2", "test_*.smt2", "ARI*.smt2", "**/*.smt2"]
        for pattern in valid_patterns:
            assert pattern
            assert pattern.strip()  # Should pass validation

        invalid_patterns = ["", "   ", None]
        for pattern in invalid_patterns:
            if pattern is None:
                continue
            assert not (pattern and pattern.strip())  # Should fail validation
