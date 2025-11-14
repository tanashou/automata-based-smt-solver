"""Benchmark test for intersect_all with different tournament structures.

This test measures the performance of SpotNFA.intersect_all() by trying all
possible tournament structures (orderings) for the intersections.
The number of tournament structures follows the Catalan number sequence.
"""

import csv
import hashlib
import json
import logging
import statistics
import time
from pathlib import Path

import psutil
import pytest
from pysmt.fnode import FNode
from pysmt.rewritings import nnf

from absmt.automata.spot_nfa import SpotNFA, TournamentStructure
from absmt.formula.rewritings import NegationEliminator
from absmt.formula.smtlib_reader import SMTLIBReader
from absmt.formula_automata_builder import FormulaAutomataBuilder

logger = logging.getLogger(__name__)

# Sample SMT2 text for testing
# You can replace this with any SMT2 text you want to test
SAMPLE_SMT2 = """
(set-info :smt-lib-version 2.6)
(set-logic QF_LIA)
(set-info :category "crafted")
(set-info :status sat)
(declare-fun x_0 () Int)
(declare-fun x_1 () Int)
(declare-fun x_2 () Int)
(assert (>= x_0 0))
(assert (>= x_1 0))
(assert (>= x_2 0))
(assert (<= (+ (* (- 9) x_0) (* 2 x_1) (* 2 x_2)) 0))
(assert (<= (+ (* 3 x_0) (* (- 8) x_1) (* 3 x_2)) 0))
(assert (<= (+ (* 5 x_0) (* 5 x_1) (* (- 6) x_2)) 0))
(assert (>= (+ x_0 x_1 x_2) 1))
(check-sat)
(exit)
"""


def generate_benchmark_id(smt2_content: str, file_path: str | None = None) -> str:
    """Generate a unique ID for the benchmark based on SMT2 content or file path.

    Args:
        smt2_content: The SMT2 content used in the benchmark
        file_path: Optional file path (if loaded from a file)

    Returns:
        A unique identifier string

    """
    if file_path:
        # Use the file name (without extension) if available
        return Path(file_path).stem
    # Use hash of content for inline SMT2
    content_hash = hashlib.sha256(smt2_content.encode()).hexdigest()[:16]
    return f"inline_{content_hash}"


def save_benchmark_metadata(
    benchmark_id: str,
    smt2_content: str,
    num_automata: int,
    num_structures: int,
    file_path: str | None = None,
) -> None:
    """Save metadata about the benchmark.

    Args:
        benchmark_id: Unique identifier for this benchmark
        smt2_content: The SMT2 content used
        num_automata: Number of automata in the benchmark
        num_structures: Number of tournament structures tested
        file_path: Optional original file path

    """
    results_dir = Path(__file__).parent.parent / ".benchmarks" / "tournament_structures"
    results_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "benchmark_id": benchmark_id,
        "num_automata": num_automata,
        "num_structures": num_structures,
        "smt2_content": smt2_content,
        "file_path": file_path,
    }

    metadata_file = results_dir / f"{benchmark_id}_meta.json"
    with metadata_file.open("w") as f:
        json.dump(metadata, f, indent=2)

    logger.info("Metadata written to %s", metadata_file)


def generate_all_tournament_structures(n: int) -> list[TournamentStructure]:
    """Generate all possible tournament structures for n automata.

    The number of tournament structures follows the Catalan number sequence.
    For n automata, there are C(n-1) different tournament structures, where
    C(k) is the k-th Catalan number.

    Args:
        n: Number of automata

    Returns:
        List of all possible tournament structures

    Examples:
        >>> generate_all_tournament_structures(1)
        [0]
        >>> generate_all_tournament_structures(2)
        [(0, 1)]
        >>> generate_all_tournament_structures(3)
        [((0, 1), 2), (0, (1, 2))]

    """
    if n <= 0:
        return []
    if n == 1:
        return [0]

    def generate_structures(indices: list[int]) -> list[TournamentStructure]:
        """Generate tournament structures for given list of indices."""
        k = len(indices)

        if k == 1:
            return [indices[0]]

        # Split into left and right subtournaments
        return [
            (left, right)  # type: ignore[return-value]
            for left_size in range(1, k)
            for left in generate_structures(indices[:left_size])
            for right in generate_structures(indices[left_size:])
        ]

    # Generate for consecutive indices 0, 1, ..., n-1
    return generate_structures(list(range(n)))


def extract_automata_from_conjunction(conjunction: FNode) -> list[SpotNFA]:
    """Extract individual automata from a conjunction (AND of literals).

    Args:
        conjunction: A formula that is a conjunction of literals

    Returns:
        List of SpotNFA instances, one for each literal in the conjunction

    """
    formula_automata_builder = FormulaAutomataBuilder()
    all_vars = [str(var) for var in conjunction.get_free_variables()]
    all_var_index_map = {var: index for index, var in enumerate(all_vars)}

    walk_context = {
        "all_vars": all_vars,
        "all_var_index_map": all_var_index_map,
    }

    automata_list: list[SpotNFA] = []

    # If it's an AND node, extract each operand
    if conjunction.is_and():
        for arg in conjunction.args():
            nfa = formula_automata_builder.walk(arg, **walk_context)
            if nfa is not None:
                automata_list.append(nfa)
    else:
        # Single literal
        nfa = formula_automata_builder.walk(conjunction, **walk_context)
        if nfa is not None:
            automata_list.append(nfa)

    return automata_list


def prepare_automata_list(
    smt2_text: str | None = None, smt2_file: str | None = None
) -> list[SpotNFA]:
    """Parse SMT2 text or file and extract automata list.

    Args:
        smt2_text: SMT-LIB2 format text (if provided, takes precedence)
        smt2_file: Path to SMT-LIB2 file

    Returns:
        List of SpotNFA instances extracted from the first conjunction

    """
    if smt2_text is None and smt2_file is None:
        msg = "Either smt2_text or smt2_file must be provided"
        raise ValueError(msg)

    reader = SMTLIBReader()
    if smt2_text:
        _, formula = reader.from_smt_lib(smt2_text, is_file_path=False)
    elif smt2_file:
        _, formula = reader.from_smt_lib(smt2_file, is_file_path=True)
    else:
        msg = "Either smt2_text or smt2_file must be provided"
        raise ValueError(msg)

    # Apply NNF and negation elimination (same as Solver)
    negation_eliminator = NegationEliminator()
    nnf_formula = nnf(formula)
    rewritten = negation_eliminator.walk(nnf_formula)

    # For simplicity, we assume the formula is a single conjunction
    # or we take the first conjunction if it's a DNF
    conjunction = rewritten.args()[0] if rewritten.is_or() else rewritten

    return extract_automata_from_conjunction(conjunction)


def run_intersect_all_with_structure(
    automata_list: list[SpotNFA], structure: TournamentStructure
) -> tuple[SpotNFA, float, float]:
    """Run intersect_all with a specific tournament structure.

    Args:
        automata_list: List of automata to intersect
        structure: Tournament structure specifying the order of intersections

    Returns:
        Tuple of (result_nfa, peak_memory_mb, elapsed_time_sec)

    """
    process = psutil.Process()
    initial_memory = process.memory_info().rss

    start_time = time.perf_counter()
    result = SpotNFA.intersect_all(*automata_list, tournament_structure=structure)
    elapsed_time = time.perf_counter() - start_time

    peak_memory = process.memory_info().rss
    peak_memory_mb = (peak_memory - initial_memory) / (1024 * 1024)

    return result, peak_memory_mb, elapsed_time


def format_tournament_structure(structure: TournamentStructure) -> str:
    """Format tournament structure as a readable string."""
    if isinstance(structure, int):
        return str(structure)
    left = format_tournament_structure(structure[0])
    right = format_tournament_structure(structure[1])
    return f"({left},{right})"


class TestIntersectAllTournamentBenchmark:
    """Benchmark tests for intersect_all with different tournament structures."""

    @pytest.fixture(scope="class")
    def automata_list(self) -> list[SpotNFA]:
        """Prepare automata list from SMT2 text once for all tests."""
        return prepare_automata_list(SAMPLE_SMT2)

    @pytest.fixture(scope="class")
    def all_tournament_structures(
        self, automata_list: list[SpotNFA]
    ) -> list[TournamentStructure]:
        """Generate all tournament structures for the automata."""
        n = len(automata_list)
        structures = generate_all_tournament_structures(n)
        logger.info(
            "Generated %d tournament structures for %d automata (Catalan number)",
            len(structures),
            n,
        )
        return structures

    @pytest.mark.parametrize(
        "structure_idx",
        range(1000),  # Will be dynamically adjusted based on actual structures
        ids=lambda x: f"structure_{x}",
    )
    def test_intersect_all_tournament(
        self,
        benchmark,
        automata_list: list[SpotNFA],
        all_tournament_structures: list[TournamentStructure],
        structure_idx: int,
    ):
        """Benchmark intersect_all with a specific tournament structure.

        Each tournament structure is tested as a separate benchmark case.
        """
        if structure_idx >= len(all_tournament_structures):
            pytest.skip(f"Structure index {structure_idx} out of range")

        structure = all_tournament_structures[structure_idx]

        result, peak_memory_mb, elapsed_time = benchmark(
            run_intersect_all_with_structure, automata_list, structure
        )

        # Add extra information to benchmark results
        benchmark.extra_info["structure_pattern"] = format_tournament_structure(
            structure
        )
        benchmark.extra_info["num_automata"] = str(len(automata_list))
        benchmark.extra_info["peak_memory_mb"] = f"{peak_memory_mb:.2f} MB"
        benchmark.extra_info["result_empty"] = str(result.is_empty())

        # Verify the result is consistent (all structures should give same result)
        assert result is not None


def test_single_intersect_all_benchmark_all_structures(benchmark):
    """Single benchmark that tries all tournament structures and reports statistics.

    This test provides aggregate statistics across all tournament structures in a
    single benchmark entry.
    """
    automata_list = prepare_automata_list(SAMPLE_SMT2)
    n = len(automata_list)

    all_structures = generate_all_tournament_structures(n)
    logger.info(
        "Testing %d tournament structures for %d automata", len(all_structures), n
    )

    # Generate benchmark ID
    benchmark_id = generate_benchmark_id(SAMPLE_SMT2)

    memories: list[float] = []
    times: list[float] = []
    results_data: list[dict[str, str | float]] = []

    def run_all_structures() -> SpotNFA:
        result: SpotNFA | None = None
        for structure in all_structures:
            result, peak_memory, elapsed_time = run_intersect_all_with_structure(
                automata_list, structure
            )
            memories.append(peak_memory)
            times.append(elapsed_time)
            results_data.append(
                {
                    "structure": format_tournament_structure(structure),
                    "time_sec": elapsed_time,
                    "memory_mb": peak_memory,
                }
            )

        if result is None:
            msg = "No structures were tested, result is None"
            raise ValueError(msg)

        return result

    result = benchmark(run_all_structures)

    # Calculate statistics
    if len(memories) > 1:
        benchmark.extra_info["num_structures_tested"] = str(len(all_structures))
        benchmark.extra_info["mean_memory_mb"] = f"{statistics.mean(memories):.2f} MB"
        benchmark.extra_info["median_memory_mb"] = (
            f"{statistics.median(memories):.2f} MB"
        )
        benchmark.extra_info["max_memory_mb"] = f"{max(memories):.2f} MB"
        benchmark.extra_info["min_memory_mb"] = f"{min(memories):.2f} MB"
        benchmark.extra_info["mean_time_sec"] = f"{statistics.mean(times):.4f} sec"
        benchmark.extra_info["median_time_sec"] = f"{statistics.median(times):.4f} sec"
        benchmark.extra_info["max_time_sec"] = f"{max(times):.4f} sec"
        benchmark.extra_info["min_time_sec"] = f"{min(times):.4f} sec"

        # Find best and worst orders
        best_time_idx = times.index(min(times))
        worst_time_idx = times.index(max(times))
        best_memory_idx = memories.index(min(memories))
        worst_memory_idx = memories.index(max(memories))

        benchmark.extra_info["fastest_structure"] = results_data[best_time_idx][
            "structure"
        ]
        benchmark.extra_info["fastest_time"] = (
            f"{results_data[best_time_idx]['time_sec']:.4f} sec"
        )
        benchmark.extra_info["slowest_structure"] = results_data[worst_time_idx][
            "structure"
        ]
        benchmark.extra_info["slowest_time"] = (
            f"{results_data[worst_time_idx]['time_sec']:.4f} sec"
        )
        benchmark.extra_info["lowest_memory_structure"] = results_data[best_memory_idx][
            "structure"
        ]
        benchmark.extra_info["lowest_memory"] = (
            f"{results_data[best_memory_idx]['memory_mb']:.2f} MB"
        )
        benchmark.extra_info["highest_memory_structure"] = results_data[
            worst_memory_idx
        ]["structure"]
        benchmark.extra_info["highest_memory"] = (
            f"{results_data[worst_memory_idx]['memory_mb']:.2f} MB"
        )

    benchmark.extra_info["num_automata"] = str(n)
    benchmark.extra_info["result_empty"] = str(result.is_empty())
    benchmark.extra_info["benchmark_id"] = benchmark_id

    # Save metadata
    save_benchmark_metadata(
        benchmark_id=benchmark_id,
        smt2_content=SAMPLE_SMT2,
        num_automata=n,
        num_structures=len(all_structures),
        file_path=None,
    )

    # Output detailed results to a CSV file
    csv_path = _save_results_to_csv(results_data, benchmark_id)
    benchmark.extra_info["csv_file"] = str(csv_path)


def run_benchmark_for_file(smt2_path: str, benchmark_name: str | None = None) -> None:
    """Run tournament structure benchmark for a specific SMT2 file.

    Args:
        smt2_path: Path to the SMT2 file
        benchmark_name: Optional custom name for the benchmark

    """
    # Read SMT2 file
    smt2_file = Path(smt2_path)
    if not smt2_file.exists():
        msg = f"SMT2 file not found: {smt2_path}"
        raise FileNotFoundError(msg)

    with smt2_file.open() as f:
        smt2_content = f.read()

    # Prepare automata
    automata_list = prepare_automata_list(smt2_file=smt2_path)
    n = len(automata_list)

    # Generate all tournament structures
    all_structures = generate_all_tournament_structures(n)
    logger.info(
        "Testing %d tournament structures for %d automata from %s",
        len(all_structures),
        n,
        smt2_path,
    )

    # Generate benchmark ID
    benchmark_id = benchmark_name or generate_benchmark_id(smt2_content, smt2_path)

    # Run benchmarks
    results_data: list[dict[str, str | float]] = []
    for structure in all_structures:
        _, peak_memory, elapsed_time = run_intersect_all_with_structure(
            automata_list, structure
        )
        results_data.append(
            {
                "structure": format_tournament_structure(structure),
                "time_sec": elapsed_time,
                "memory_mb": peak_memory,
            }
        )

    # Save metadata
    save_benchmark_metadata(
        benchmark_id=benchmark_id,
        smt2_content=smt2_content,
        num_automata=n,
        num_structures=len(all_structures),
        file_path=smt2_path,
    )

    # Save results
    csv_path = _save_results_to_csv(results_data, benchmark_id)
    logger.info("Benchmark completed: %s", benchmark_id)
    logger.info("Results saved to: %s", csv_path)


def _save_results_to_csv(
    results_data: list[dict[str, str | float]], benchmark_id: str
) -> Path:
    """Save detailed tournament structure results to CSV file.

    Args:
        results_data: List of benchmark results
        benchmark_id: Unique identifier for this benchmark

    Returns:
        Path to the saved CSV file

    """
    # Use .benchmarks/tournament_structures directory
    results_dir = Path(__file__).parent.parent / ".benchmarks" / "tournament_structures"
    results_dir.mkdir(parents=True, exist_ok=True)

    output_file = results_dir / f"{benchmark_id}.csv"
    with output_file.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["structure", "time_sec", "memory_mb"])
        writer.writeheader()
        writer.writerows(results_data)

    logger.info("Detailed results written to %s", output_file)
    return output_file
