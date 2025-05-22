from pathlib import Path

import pytest

from automata_based_smt_solver.formula.smtlib_reader import SMTLIBReader


@pytest.fixture
def reader():
    """Return a Reader instance for testing."""
    return SMTLIBReader()


@pytest.fixture
def fixtures_dir():
    """Return the path to the fixtures directory."""
    project_root = Path(__file__).resolve().parents[2]  # Navigate to project root
    return project_root / "tests" / "fixtures"


@pytest.fixture
def benchmark_dir(fixtures_dir):
    """Return the path to the QF_LIA/check benchmark directory."""
    benchmark_dir = fixtures_dir / "benchmarks" / "QF_LIA" / "check"
    if not benchmark_dir.exists():
        pytest.skip(f"Required test directory {benchmark_dir} does not exist")
    return benchmark_dir


@pytest.fixture
def benchmark_file_paths(benchmark_dir):
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
        file_path = benchmark_dir / file_name
        if file_path.exists():
            result.append(file_path)

    if not result:
        pytest.skip("No benchmark files found in the fixtures directory")

    return result


@pytest.fixture
def int_incompleteness1_path(benchmark_dir):
    """Return a single benchmark file path for testing."""
    file_path = benchmark_dir / "int_incompleteness1.smt2"

    if not file_path.exists():
        pytest.skip(f"Required benchmark file {file_path} not found")

    return file_path


@pytest.fixture
def bignum_lia1_path(benchmark_dir):
    """Return a single benchmark file path for testing."""
    file_path = benchmark_dir / "bignum_lia1.smt2"

    if not file_path.exists():
        pytest.skip(f"Required benchmark file {file_path} not found")

    return file_path


@pytest.fixture(params=["sat", "unsat", "unknown"])
def benchmark_files_by_status(request, benchmark_dir):
    """Parameterized fixture returning benchmark files by status."""
    status = request.param

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


@pytest.fixture
def int_incompleteness1_formula(reader, int_incompleteness1_path):
    """Parse the benchmark file and return the formula."""
    _, formula = reader.from_smt_lib(str(int_incompleteness1_path), is_file_path=True)
    return formula


@pytest.fixture
def bignum_lia1_formula(reader, bignum_lia1_path):
    """Parse the benchmark file and return the formula."""
    _, formula = reader.from_smt_lib(str(bignum_lia1_path), is_file_path=True)
    return formula


@pytest.fixture
def all_parsed_formulas(reader, benchmark_file_paths):
    """Parse all benchmark files and return their formulas."""
    results = []
    for file_path in benchmark_file_paths:
        _, formula = reader.from_smt_lib(str(file_path), is_file_path=True)
        results.append((file_path.name, formula))
    return results
