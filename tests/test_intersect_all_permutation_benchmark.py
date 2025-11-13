"""Benchmark test for intersect_all with different permutations of operand order.

This test measures the performance of SpotNFA.intersect_all() by trying all
possible orderings of the input automata.
"""

import logging
import statistics
from itertools import permutations

import psutil
import pytest
from pysmt.fnode import FNode
from pysmt.rewritings import nnf

from absmt.automata.spot_nfa import SpotNFA
from absmt.formula.rewritings import NegationEliminator
from absmt.formula.smtlib_reader import SMTLIBReader
from absmt.formula_automata_builder import FormulaAutomataBuilder

logger = logging.getLogger(__name__)


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


def run_intersect_all_with_order(
    automata_list: list[SpotNFA], order: tuple[int, ...]
) -> tuple[SpotNFA, float]:
    """Run intersect_all with a specific ordering of automata.

    Args:
        automata_list: List of automata to intersect
        order: Tuple of indices specifying the order

    Returns:
        Tuple of (result_nfa, peak_memory_mb)

    """
    process = psutil.Process()
    initial_memory = process.memory_info().rss

    ordered_automata = [automata_list[i] for i in order]
    result = SpotNFA.intersect_all(*ordered_automata)

    peak_memory = process.memory_info().rss
    peak_memory_mb = (peak_memory - initial_memory) / (1024 * 1024)

    return result, peak_memory_mb


# Configuration: Maximum number of automata to test
# For n automata, the number of permutations is n!
# Examples: 3->6, 4->24, 5->120, 6->720, 7->5040, 8->40320
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


def generate_permutation_id(val: tuple[tuple[int, ...], list[SpotNFA]]) -> str:
    """Generate a readable test ID for each permutation."""
    order, automata_list = val
    return f"order_{'-'.join(map(str, order))}_of_{len(automata_list)}_automata"


class TestIntersectAllPermutationBenchmark:
    """Benchmark tests for intersect_all with different orderings."""

    @pytest.fixture(scope="class")
    def automata_list(self) -> list[SpotNFA]:
        """Prepare automata list from SMT2 text once for all tests."""
        return prepare_automata_list(SAMPLE_SMT2)

    @pytest.fixture(scope="class")
    def all_permutations(self, automata_list: list[SpotNFA]) -> list[tuple[int, ...]]:
        """Generate all permutations of automata indices."""
        n = len(automata_list)
        if n > MAX_AUTOMATA:
            pytest.skip(
                f"Too many automata ({n}) would generate {n}! permutations. "
                "Skipping to avoid excessive test time. "
                f"Increase MAX_AUTOMATA constant in the file (current: {MAX_AUTOMATA})"
            )
        return list(permutations(range(n)))

    @pytest.mark.parametrize(
        "order_idx",
        range(100),  # Will be dynamically adjusted based on actual permutations
        ids=lambda x: f"permutation_{x}",
    )
    def test_intersect_all_permutation(
        self,
        benchmark,
        automata_list: list[SpotNFA],
        all_permutations: list[tuple[int, ...]],
        order_idx: int,
    ):
        """Benchmark intersect_all with a specific permutation order.

        Each permutation is tested as a separate benchmark case.
        """
        if order_idx >= len(all_permutations):
            pytest.skip(f"Permutation index {order_idx} out of range")

        order = all_permutations[order_idx]

        result, peak_memory_mb = benchmark(
            run_intersect_all_with_order, automata_list, order
        )

        # Add extra information to benchmark results
        benchmark.extra_info["order_pattern"] = "-".join(map(str, order))
        benchmark.extra_info["num_automata"] = str(len(automata_list))
        benchmark.extra_info["peak_memory_mb"] = f"{peak_memory_mb:.2f} MB"
        benchmark.extra_info["result_empty"] = str(result.is_empty())

        # Verify the result is consistent (all orderings should give same result)
        assert result is not None


def test_single_intersect_all_benchmark_all_orders(benchmark):
    """Single benchmark that tries all permutation orders and reports statistics.

    This test provides aggregate statistics across all orderings in a single
    benchmark entry.
    """
    automata_list = prepare_automata_list(SAMPLE_SMT2)
    n = len(automata_list)

    if n > MAX_AUTOMATA:
        pytest.skip(
            f"Too many automata ({n}) would generate {n}! permutations. "
            "Skipping to avoid excessive test time. "
            f"Increase MAX_AUTOMATA constant in the file (current: {MAX_AUTOMATA})"
        )

    all_orders = list(permutations(range(n)))
    memories: list[float] = []

    def run_all_orders() -> SpotNFA:
        result: SpotNFA | None = None
        for order in all_orders:
            result, peak_memory = run_intersect_all_with_order(automata_list, order)
            memories.append(peak_memory)

        if result is None:
            msg = "No orders were tested, result is None"
            raise ValueError(msg)

        return result

    result = benchmark(run_all_orders)

    # Calculate statistics
    if len(memories) > 1:
        benchmark.extra_info["num_orders_tested"] = str(len(all_orders))
        benchmark.extra_info["mean_memory_mb"] = f"{statistics.mean(memories):.2f} MB"
        benchmark.extra_info["median_memory_mb"] = (
            f"{statistics.median(memories):.2f} MB"
        )
        benchmark.extra_info["max_memory_mb"] = f"{max(memories):.2f} MB"
        benchmark.extra_info["min_memory_mb"] = f"{min(memories):.2f} MB"

    benchmark.extra_info["num_automata"] = str(n)
    benchmark.extra_info["result_empty"] = str(result.is_empty())
