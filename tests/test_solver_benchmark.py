from pathlib import Path

import pytest

from absmt.formula.smtlib_reader import SMTLIBReader
from absmt.sat_status import SatStatus
from absmt.solver import Solver


def _resolve_prime_cone_paths() -> list[Path]:
    """Return resolved paths from benchmarks/paths/prime-cone-sat.txt.

    If the list file or the referenced .smt2 files are missing, the test will be
    skipped to make the benchmark best-effort in CI environments.
    """
    repo_root = Path(__file__).resolve().parents[1]
    list_file = repo_root / "benchmarks" / "paths" / "prime-cone-sat.txt"
    if not list_file.exists():
        pytest.skip(f"List file not found: {list_file}", allow_module_level=True)

    base_dir = list_file.parent
    paths: list[Path] = []
    with list_file.open("r", encoding="utf-8") as fh:
        for raw_line in fh:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            p = (base_dir / line).resolve()
            if p.exists():
                paths.append(p)

    if not paths:
        pytest.skip(
            f"No referenced .smt2 files found in {list_file}", allow_module_level=True
        )
    return paths


@pytest.mark.parametrize("path", _resolve_prime_cone_paths())
def test_solver_benchmark(benchmark, path: Path):
    """Benchmark solver runtime for each SMT2 file listed in prime-cone-sat.txt.

    For each file the test will:
      - parse the file using `SMTLIBReader.from_smt_lib(..., is_file_path=True)`
      - create a fresh `Solver`, add the parsed formula, and run `solver.solve()`
      - measure the runtime of the callable (parsing + solving) using the
        `benchmark` fixture provided by `pytest-benchmark`.
    """

    def run(path_str: str) -> tuple[SatStatus, SatStatus]:
        reader = SMTLIBReader()
        solver = Solver()
        expected_status, formula = reader.from_smt_lib(path_str, is_file_path=True)
        # add formula then solve; this measures the end-to-end parse+solve time
        solver.add(formula)
        return expected_status, solver.solve()

    # benchmark the run callable; pass the file path as argument
    expected_status, actual_status = benchmark(run, str(path))

    # Basic sanity checks: solver returned a SatStatus and it matches expected
    assert isinstance(actual_status, SatStatus)
    assert actual_status == expected_status
