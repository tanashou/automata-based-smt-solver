"""Benchmark test for intersect_all with different tournament structures.

This test measures the performance of SpotNFA.intersect_all() by trying all
possible tournament structures (orderings) for the intersections.
The number of tournament structures follows the Catalan number sequence.
"""

import csv
import functools
import hashlib
import json
import logging
import time
import tracemalloc
from pathlib import Path

from pysmt.fnode import FNode
from pysmt.rewritings import nnf

from absmt.automata.spot_nfa import SpotNFA, TournamentStructure
from absmt.formula.rewritings import NegationEliminator
from absmt.formula.smtlib_reader import SMTLIBReader
from absmt.formula_automata_builder import FormulaAutomataBuilder

logger = logging.getLogger(__name__)

"""Tournament structure generation for benchmark testing.

This module provides efficient generation of all unique tournament structures
using dynamic programming with memoization.
"""


@functools.cache
def _normalize_fast(structure: TournamentStructure) -> TournamentStructure:
    """トーナメント構造を高速に正規化する (メモ化付き).

    Args:
        structure: 正規化するトーナメント構造

    Returns:
        正規化されたトーナメント構造

    Note:
        intは常にtupleより小さいとみなす。
        lru_cacheによりメモ化されるため、同じ構造の正規化は1度だけ計算される。

    """
    if isinstance(structure, int):
        return structure

    norm_left = _normalize_fast(structure[0])
    norm_right = _normalize_fast(structure[1])

    is_left_int = isinstance(norm_left, int)
    is_right_int = isinstance(norm_right, int)

    swap = False
    if is_left_int and is_right_int:
        # 両方 int: 数値で比較
        if norm_left > norm_right:
            swap = True
    elif not is_left_int and not is_right_int:
        # 両方 tuple: 再帰的に比較
        cmp = _compare_structures(norm_left[0], norm_right[0])
        if cmp > 0 or (
            cmp == 0 and _compare_structures(norm_left[1], norm_right[1]) > 0
        ):
            swap = True
    elif not is_left_int and is_right_int:
        # 左が tuple, 右が int: int < tuple なので swap
        swap = True

    if swap:
        return (norm_right, norm_left)
    return (norm_left, norm_right)


def _compare_structures(left: TournamentStructure, right: TournamentStructure) -> int:
    """2つのトーナメント構造を比較する.

    Args:
        left: 左側の構造
        right: 右側の構造

    Returns:
        left < right なら -1, left == right なら 0, left > right なら 1

    """
    is_left_int = isinstance(left, int)
    is_right_int = isinstance(right, int)

    if is_left_int and is_right_int:
        return (left > right) - (left < right)
    if is_left_int:
        # int < tuple
        return -1
    if is_right_int:
        # tuple > int
        return 1

    # 両方 tuple: 再帰的に比較
    left_cmp = _compare_structures(left[0], right[0])
    if left_cmp != 0:
        return left_cmp
    return _compare_structures(left[1], right[1])


@functools.cache
def generate_labeled_normalized_structures(
    indices: frozenset[int],
) -> set[TournamentStructure]:
    """ラベル付き正規化トーナメント構造を動的計画法で生成する.

    Args:
        indices: 使用する数字の集合 (例: {0, 1, 2})

    Returns:
        生成された全ての正規化済みトーナメント構造の集合

    Note:
        この関数は動的計画法とメモ化を使用して、順列を全探索するよりも
        遥かに高速に全てのユニークな構造を生成します。
        frozensetは変更不可なセットで、lru_cacheのキーとして使用できます。

    """
    # ベースケース: 要素が1つ
    k = len(indices)
    if k == 1:
        return {next(iter(indices))}

    # 再帰ステップ: この indices セットから作られる全構造を格納
    results: set[TournamentStructure] = set()

    indices_list = list(indices)

    # indices を 2つの空でない部分集合 (left_set, right_set) に分割する
    # 2^k 通りの部分集合をすべて試す
    for i in range(1, 1 << k):
        left_subset: set[int] = set()
        right_subset: set[int] = set()

        for j in range(k):
            if (i >> j) & 1:
                # i の j ビット目が 1 なら left_subset に
                left_subset.add(indices_list[j])
            else:
                # 0 なら right_subset に
                right_subset.add(indices_list[j])

        # どちらかが空集合になる分割は無効
        if not left_subset or not right_subset:
            continue

        # 再帰呼び出しで部分集合から構造を生成
        left_structures = generate_labeled_normalized_structures(frozenset(left_subset))
        right_structures = generate_labeled_normalized_structures(
            frozenset(right_subset)
        )

        # 2つの構造セットから全てのペアを作り、正規化して追加
        for left_struct in left_structures:
            for right_struct in right_structures:
                normalized = _normalize_fast((left_struct, right_struct))
                results.add(normalized)

    return results


def generate_all_tournament_structures(n: int) -> list[TournamentStructure]:
    """n個の要素に対する全てのユニークなトーナメント構造を生成する.

    Args:
        n: オートマトンの数

    Returns:
        生成された全てのトーナメント構造のリスト

    Note:
        この関数は動的計画法ベースの実装を使用し、
        従来の順列ベースのアプローチよりも高速です。

    """
    if n <= 0:
        return []
    if n == 1:
        return [0]

    initial_indices = frozenset(range(n))
    structures_set = generate_labeled_normalized_structures(initial_indices)

    return list(structures_set)


def format_tournament_structure(structure: TournamentStructure) -> str:
    """トーナメント構造を読みやすい文字列としてフォーマットする.

    Args:
        structure: フォーマットするトーナメント構造

    Returns:
        フォーマットされた文字列 (例: "(0,(1,2))")

    """
    if isinstance(structure, int):
        return str(structure)
    left = format_tournament_structure(structure[0])
    right = format_tournament_structure(structure[1])
    return f"({left},{right})"


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

    base_metadata_file = results_dir / f"{benchmark_id}_meta.json"
    metadata_file = _get_unique_file_path(base_metadata_file)

    with metadata_file.open("w") as f:
        json.dump(metadata, f, indent=2)

    logger.info("Metadata written to %s", metadata_file)


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
) -> tuple[SpotNFA | None, float, float, dict[str, int]]:
    """Run intersect_all with a specific tournament structure.

    Args:
        automata_list: List of automata to intersect
        structure: Tournament structure specifying the order of intersections

    Returns:
        Tuple of (result_nfa, peak_memory_mb, elapsed_time_sec, state_counts)
        where result_nfa can be None if the intersection is empty,
        and state_counts is a dict mapping structure representations to state counts

    Note:
        Uses tracemalloc to measure peak memory usage during the operation.
        This accurately captures the maximum memory allocated, even if garbage
        collection occurs before the operation completes.

    """
    # Dictionary to store state counts for each intermediate result
    state_counts: dict[str, int] = {}

    # Record initial automaton sizes
    for i, nfa in enumerate(automata_list):
        state_counts[str(i)] = nfa.num_states()

    # Start memory tracing to capture peak memory
    tracemalloc.start()

    try:
        start_time = time.perf_counter()
        result = SpotNFA.intersect_all(
            *automata_list,
            tournament_structure=structure,
            state_counts=state_counts,
        )
        elapsed_time = time.perf_counter() - start_time

        # Get peak memory usage (in bytes)
        current, peak = tracemalloc.get_traced_memory()
        peak_memory_mb = peak / (1024 * 1024)

    finally:
        # Always stop tracing to free resources
        tracemalloc.stop()

    return result, peak_memory_mb, elapsed_time, state_counts


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
    logger.info("=" * 80)
    logger.info(
        "Starting benchmark: %d tournament structures for %d automata",
        len(all_structures),
        n,
    )
    logger.info(
        "Source file: %s",
        smt2_path,
    )
    logger.info("=" * 80)

    # Generate benchmark ID
    benchmark_id = benchmark_name or generate_benchmark_id(smt2_content, smt2_path)

    # Run benchmarks
    results_data: list[dict[str, str | float]] = []
    total = len(all_structures)

    for idx, structure in enumerate(all_structures, 1):
        _, peak_memory, elapsed_time, state_counts = run_intersect_all_with_structure(
            automata_list, structure
        )
        results_data.append(
            {
                "structure": format_tournament_structure(structure),
                "time_sec": elapsed_time,
                "memory_mb": peak_memory,
                "state_counts": str(state_counts),
            }
        )

        # Progress logging every 10% or at significant milestones
        if idx % max(1, total // 10) == 0 or idx == total:
            logger.info(
                "Progress: %d/%d (%.1f%%)",
                idx,
                total,
                (idx / total) * 100,
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
    logger.info("=" * 80)
    logger.info("✓ Benchmark completed: %s", benchmark_id)
    logger.info("Results saved to: %s", csv_path)
    logger.info("=" * 80)


def _get_unique_file_path(base_path: Path) -> Path:
    """Get a unique file path by adding a counter if the file already exists.

    Args:
        base_path: The base file path (without counter)

    Returns:
        A unique file path that doesn't exist yet

    Example:
        If "results.csv" exists, returns "results_1.csv"
        If "results_1.csv" also exists, returns "results_2.csv", etc.

    """
    if not base_path.exists():
        return base_path

    stem = base_path.stem
    suffix = base_path.suffix
    parent = base_path.parent

    counter = 1
    while True:
        new_path = parent / f"{stem}_{counter}{suffix}"
        if not new_path.exists():
            return new_path
        counter += 1


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

    base_output_file = results_dir / f"{benchmark_id}.csv"
    output_file = _get_unique_file_path(base_output_file)

    with output_file.open("w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["structure", "time_sec", "memory_mb", "state_counts"]
        )
        writer.writeheader()
        writer.writerows(results_data)

    logger.info("Detailed results written to %s", output_file)
    return output_file
