"""Benchmark test for intersect_all with different tournament structures.

This test measures the performance of SpotNFA.intersect_all() by trying all
possible tournament structures (orderings) for the intersections.
The number of tournament structures follows the Catalan number sequence.
"""

import csv
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


def prepare_automata_list(smt2_text: str) -> list[SpotNFA]:
    """Parse SMT2 text and extract automata list.

    Args:
        smt2_text: SMT-LIB2 format text

    Returns:
        List of SpotNFA instances extracted from the first conjunction

    """
    reader = SMTLIBReader()
    _, formula = reader.from_smt_lib(smt2_text, is_file_path=False)

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


# Configuration: Maximum number of automata to test
# For n automata, the number of tournament structures follows Catalan numbers
# Examples: 2->1, 3->2, 4->5, 5->14, 6->42, 7->132, 8->429
MAX_AUTOMATA = 10  # Set this to allow testing larger cases

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
        if n > MAX_AUTOMATA:
            pytest.skip(
                f"Too many automata ({n}). "
                "Skipping to avoid excessive test time. "
                f"Increase MAX_AUTOMATA constant in the file (current: {MAX_AUTOMATA})"
            )
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

    if n > MAX_AUTOMATA:
        pytest.skip(
            f"Too many automata ({n}). "
            "Skipping to avoid excessive test time. "
            f"Increase MAX_AUTOMATA constant in the file (current: {MAX_AUTOMATA})"
        )

    all_structures = generate_all_tournament_structures(n)
    logger.info(
        "Testing %d tournament structures for %d automata", len(all_structures), n
    )

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

    # Output detailed results to a CSV file
    _save_results_to_csv(results_data)


def _save_results_to_csv(results_data: list[dict[str, str | float]]) -> None:
    """Save detailed tournament structure results to CSV file."""
    output_file = Path("benchmark_tournament_results.csv")
    with output_file.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["structure", "time_sec", "memory_mb"])
        writer.writeheader()
        writer.writerows(results_data)

    logger.info("Detailed results written to %s", output_file)
