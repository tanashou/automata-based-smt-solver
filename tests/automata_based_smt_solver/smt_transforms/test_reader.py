from pathlib import Path

import pytest
from pysmt.fnode import FNode

from automata_based_smt_solver.sat_status import SatStatus
from automata_based_smt_solver.smt_transforms.reader import Reader


class TestReader:
    @pytest.fixture
    def reader(self):
        """Return a Reader instance for testing."""
        return Reader()

    @pytest.fixture
    def fixtures_dir(self):
        """Return the path to the fixtures directory."""
        project_root = Path(__file__).resolve().parents[3]  # Navigate to project root
        return project_root / "tests" / "fixtures"

    @pytest.fixture
    def ensure_fixtures_dir(self, fixtures_dir):
        """Check if the fixtures directory exists and skip if it doesn't."""
        benchmark_dir = fixtures_dir / "benchmarks" / "QF_LIA" / "check"
        if not benchmark_dir.exists():
            pytest.skip(f"Required test directory {benchmark_dir} does not exist")
        return fixtures_dir

    @pytest.fixture
    def benchmark_file_paths(self, ensure_fixtures_dir):
        """Return the paths to the test benchmark files."""
        file_names = [
            "bignum_lia1.smt2",
            "bignum_lia2_unknown.smt2",
            "bignum_lia2.smt2",
            "int_incompleteness1.smt2",
            "int_incompleteness2.smt2",
            "int_incompleteness3.smt2",
        ]
        result = []
        for file_name in file_names:
            file_path = (
                ensure_fixtures_dir / "benchmarks" / "QF_LIA" / "check" / file_name
            )
            if file_path.exists():
                result.append(file_path)

        if not result:
            pytest.skip("No benchmark files found in the fixtures directory")

        return result

    @pytest.fixture
    def benchmark_file_path(self, ensure_fixtures_dir):
        """Return a single benchmark file path for testing."""
        file_path = (
            ensure_fixtures_dir / "benchmarks" / "QF_LIA" / "check" / "bignum_lia1.smt2"
        )

        if not file_path.exists():
            pytest.skip(f"Required benchmark file {file_path} not found")

        return file_path

    @pytest.fixture(params=["sat", "unsat", "unknown"])
    def benchmark_files_by_status(self, request, ensure_fixtures_dir):
        """Parameterized fixture returning benchmark files by status."""
        status = request.param
        benchmark_dir = ensure_fixtures_dir / "benchmarks" / "QF_LIA" / "check"

        # Map of status to file patterns that have that status
        status_patterns = {
            "sat": [
                "bignum_lia2.smt2",
            ],
            "unsat": [
                "bignum_lia1.smt2",
                "int_incompleteness1.smt2",
                "int_incompleteness2.smt2",
                "int_incompleteness3.smt2",
            ],
            "unknown": [
                "bignum_lia2_unknown.smt2",
            ],
        }

        # Get all matching files
        matching_files = []
        for pattern in status_patterns[status]:
            matching_files.extend(list(benchmark_dir.glob(pattern)))

        # Skip if no matching files
        if not matching_files:
            pytest.skip(f"No benchmark files with {status} status found")

        return matching_files, status

    def test_from_smt_lib_file(self, reader, benchmark_file_paths):
        """Test reading from SMT-LIB files."""
        for file_path in benchmark_file_paths:
            # Convert Path to string for pysmt compatibility
            file_path_str = str(file_path)

            # Test each benchmark file
            status, formula = reader.from_smt_lib(file_path_str, is_file=True)

            # Check formula basics (should work for all files)
            assert isinstance(formula, FNode)

            # Check that variables are properly extracted
            variables = formula.get_free_variables()
            assert len(variables) > 0, f"No variables found in {file_path.name}"

    def test_status_from_smt_files(self, reader, benchmark_files_by_status):
        """Test that status is correctly parsed from SMT-LIB files."""
        files, expected_status = benchmark_files_by_status

        for file_path in files:
            # Convert Path to string for pysmt compatibility
            file_path_str = str(file_path)

            status, _ = reader.from_smt_lib(file_path_str, is_file=True)
            assert status == SatStatus(expected_status), (
                f"Wrong status for {file_path.name}"
            )

    def test_from_smt_lib_string(self, reader):
        """Test reading from an SMT-LIB string."""
        smt_content = """
        (set-info :smt-lib-version 2.6)
        (set-info :status sat)
        (declare-fun x () Int)
        (declare-fun y () Int)
        (assert (= x y))
        (check-sat)
        """
        status, formula = reader.from_smt_lib(smt_content, is_file=False)

        # Check status
        assert status == SatStatus.SAT

        # Check formula
        assert isinstance(formula, FNode)
        assert formula.is_equals()

        # Check variables
        variables = formula.get_free_variables()
        variable_names = {str(var) for var in variables}
        assert variable_names == {"x", "y"}

    def test_unknown_status(self, reader):
        """Test reading a formula with unknown status."""
        smt_content = """
        (declare-fun x () Int)
        (assert (> x 0))
        (check-sat)
        """
        status, formula = reader.from_smt_lib(smt_content, is_file=False)

        # Status should be unknown as there's no status info
        assert status == SatStatus.UNKNOWN

        # Check formula
        assert isinstance(formula, FNode)
