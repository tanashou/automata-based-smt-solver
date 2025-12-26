# ruff: noqa: ANN001, ANN003, ARG002

import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import ClassVar

import buddy
import pysmt.operators as op
import spot
from pysmt.exceptions import (
    PysmtValueError,
)
from pysmt.fnode import FNode
from pysmt.logics import LIA, QF_LIA
from pysmt.oracles import get_logic
from pysmt.walkers import DagWalker
from pysmt.walkers.generic import handles

from absmt.automata.spot_nfa import SpotNFA, TournamentStructure
from absmt.automata_builder import AutomataBuilder
from absmt.formula import LiteralDataExtractor

logger = logging.getLogger(__name__)


class FormulaAutomataBuilder(DagWalker):
    LOGICS: ClassVar[list] = [LIA, QF_LIA]

    def __init__(self) -> None:
        super().__init__()
        self._literal_data_extractor = LiteralDataExtractor()
        self._bdict = spot.make_bdd_dict()
        self._well_formed_twa_graph = self._create_well_formed_twa_graph(self._bdict)

    @staticmethod
    def _create_well_formed_twa_graph(bdict) -> SpotNFA:
        # リテラルをオートマトンに変換すると、イプシロンは受理しないようになっている。
        # 全ての長さ1以上のビットを受理するオートマトンの補集合はイプシロンのみを
        # 受理するものになる。これは空でないと判定されるのでおかしい。
        # よって、イプシロンは受理しないようにする
        wf_graph = spot.make_twa_graph(bdict)
        wf_graph.set_buchi()

        # _END 変数の AP インデックスを取得
        end_ap = wf_graph.register_ap("_END")

        # 状態作成
        s_start = wf_graph.new_state()
        s_loop = wf_graph.new_state()
        s_sink = wf_graph.new_state()

        wf_graph.set_init_state(s_start)

        # BDD 作成
        bdd_end = buddy.bdd_ithvar(end_ap)
        bdd_not_end = buddy.bdd_nithvar(end_ap)

        # 遷移作成

        # 1. 開始状態からは !_END のみが許される。長さ1以上を強制
        # s_start --(!_END)--> s_loop
        wf_graph.new_edge(s_start, s_loop, bdd_not_end)

        # 2. ループ状態では !_END が続くか、_END で抜けるか
        # s_loop --(!_END)--> s_loop
        wf_graph.new_edge(s_loop, s_loop, bdd_not_end)

        # s_loop --(_END)--> s_sink
        wf_graph.new_edge(s_loop, s_sink, bdd_end)

        # 3. シンク状態
        # s_sink --(_END)--> s_sink (Accepting)
        wf_graph.new_edge(s_sink, s_sink, bdd_end, [0])

        return SpotNFA.from_twa_graph(wf_graph)

    def build(self, formula: FNode) -> SpotNFA | None:
        logic = get_logic(formula)
        if not any(logic <= allowed_logic for allowed_logic in self.LOGICS):
            msg = (
                "formula automata builder only "
                "supports LIA or QF_LIA without combination."
                f"(detected logic is: {logic!s})"
            )
            raise PysmtValueError(msg)

        # LIAの場合、intersectionで空オートマトンを返さないようにする
        return_explicit_empty = logic == LIA

        all_vars = [str(var) for var in formula.get_free_variables()]
        all_vars += [str(var) for var in QuantVarCollector().collect(formula)]
        all_var_index_map = {var: index for index, var in enumerate(all_vars)}
        walk_context = {
            "all_vars": all_vars,
            "all_var_index_map": all_var_index_map,
            "return_explicit_empty": return_explicit_empty,
        }
        return self.walk(formula, **walk_context)

    def _get_key(self, formula: FNode, *args: list, **kwargs) -> FNode:
        return formula

    def walk_and(self, formula: FNode, args: list[SpotNFA], **kwargs) -> SpotNFA | None:
        formula_str = formula.serialize(threshold=20)
        logger.debug(
            "Building automaton for 'and' with %d operands; formula=%s",
            len(args),
            formula_str,
        )

        tournament_struct = self._create_tournament_structure(args)
        logger.debug(
            "Tournament structure for 'and' created: %s", str(tournament_struct)
        )
        return_explicit_empty = kwargs.get("return_explicit_empty", False)
        res = SpotNFA.intersect_all(
            *args,
            tournament_structure=tournament_struct,
            return_explicit_empty=return_explicit_empty,
        )

        if res is None:
            logger.debug("Complete building for 'and': result is empty (None).")
        else:
            logger.debug("Complete building for 'and'.")
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(res.custom_log())

        return res

    def walk_or(self, formula: FNode, args: list[SpotNFA], **kwargs) -> SpotNFA | None:
        formula_str = formula.serialize(threshold=20)
        logger.debug(
            "Building automaton for 'or' with %d operands; formula=%s",
            len(args),
            formula_str,
        )
        res = SpotNFA.union_all(*args)
        if res is None:
            logger.debug("Complete building for 'or': result is empty (None).")
        else:
            logger.debug("Complete building for 'or'.")
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(res.custom_log())

        return res

    def walk_exists(
        self, formula: FNode, args: list[SpotNFA], **kwargs
    ) -> SpotNFA | None:
        if len(args) != 1:
            msg = (
                "The body of an exists expression must be represented as a single nfa. "
            )
            raise ValueError(msg)

        quantifier_vars_str = [str(var) for var in formula.quantifier_vars()]
        spot_nfa = args[0]
        spot_nfa.minimize()  # 全部展開するから最小化しておく。
        res = SpotNFA.projection(spot_nfa, quantifier_vars_str)
        logger.debug(
            "Completed building for 'exists' over vars %s; formula=%s",
            quantifier_vars_str,
            formula.serialize(threshold=20),
        )
        if res is None:
            logger.debug("Result is empty (None) after projection.")
        else:
            logger.debug("Resulting automaton after projection:")
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(res.custom_log())
        return res

    def walk_not(self, formula: FNode, args: list[SpotNFA], **kwargs) -> SpotNFA:
        if len(args) != 1:
            msg = "The body of a NOT expression must be represented as a single nfa."
            raise ValueError(msg)
        return_explicit_empty = kwargs.get("return_explicit_empty", False)
        spot_nfa = args[0]
        spot_nfa.minimize()
        res = SpotNFA.complement(spot_nfa, self._bdict)
        res = SpotNFA.intersect_all(
            res,
            self._well_formed_twa_graph,
            return_explicit_empty=return_explicit_empty,
        )
        if res is None:
            msg = "Complement resulted in an empty automaton, which should not happen."
            raise ValueError(msg)
        logger.debug(
            "Completed building for 'not'; formula=%s", formula.serialize(threshold=20)
        )
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(res.custom_log())
        return res

    @handles(op.LT, op.LE, op.EQUALS)
    def walk_literal(self, formula: FNode, args, **kwargs) -> SpotNFA:
        literal_data = self._literal_data_extractor.extract(formula)
        all_vars = kwargs["all_vars"]
        all_var_index_map = kwargs["all_var_index_map"]

        builder = AutomataBuilder(literal_data, all_vars, all_var_index_map)
        nfa = builder.build()
        res = SpotNFA(nfa, self._bdict)
        res.set_formula_data(literal_data)
        res.minimize()
        formula_str = formula.serialize(threshold=20)
        logger.debug(
            "Prepared automaton for 'literal'; formula=%s",
            formula_str,
        )
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(res.custom_log())

        return res

    @handles(
        op.SYMBOL,
        *op.CONSTANTS,
        *op.IRA_OPERATORS,
    )
    def walk_others(self, formula: FNode, args, **kwargs) -> None:
        return

    # --- Tournament Structure Creation ---
    def _create_tournament_structure(  # noqa: C901, PLR0912
        self, automata: list[SpotNFA]
    ) -> TournamentStructure:
        """Create tournament structure with multi-stage clustering.

        New Strategy:
        1. Cluster by structural similarity
        2. Treat size≥2 clusters as single "blocks" (variables = union)
        3. Combine blocks and singletons
        4. Re-cluster by common variables
        5. Within each group, order by estimated state count

        Args:
            automata: List of SpotNFA instances

        Returns:
            TournamentStructure optimized for computation order

        """
        if not automata:
            msg = "Cannot create tournament structure for empty list"
            raise ValueError(msg)

        if len(automata) == 1:
            return 0

        # Stage 1: 構造でクラスタリング
        structure_clusters = self._cluster_by_structure(automata)

        logger.debug(
            "Stage 1 (structure): %d NFAs -> %d clusters",
            len(automata),
            len(structure_clusters),
        )

        # Stage 2: サイズ≥2のクラスタを「塊」として扱う
        # ClusterBlockクラスで抽象化

        blocks: list[ClusterBlock] = []

        for cluster in structure_clusters:
            # 変数集合を計算
            all_vars = set()
            for nfa in cluster:
                all_vars.update(nfa.get_registered_ap())

            # 推定状態数を計算
            estimated = 1
            for nfa in cluster:
                estimated *= nfa.num_states()

            # サイズ≥2の場合は内部構造を構築(どの順番でもいい)
            internal_structure = None
            if len(cluster) > 1:
                nfa_to_index = {id(nfa): i for i, nfa in enumerate(automata)}
                indices = [nfa_to_index[id(nfa)] for nfa in cluster]
                internal_structure = self._build_balanced_structure_from_indices(
                    indices
                )

            blocks.append(
                ClusterBlock(
                    cluster=cluster,
                    variables=all_vars,
                    estimated_states=estimated,
                    structure=internal_structure,
                )
            )

        logger.debug("Stage 2 (blocks): Created %d blocks from clusters", len(blocks))

        # Stage 3: ブロック同士を共通変数でクラスタリング
        variable_clusters = self._cluster_blocks_by_common_variables(blocks)

        logger.debug(
            "Stage 3 (variable clustering): %d blocks -> %d groups",
            len(blocks),
            len(variable_clusters),
        )

        # Stage 4: 各グループ内で推定状態数ソート&左重心構造
        nfa_to_index = {id(nfa): i for i, nfa in enumerate(automata)}
        group_structures = []

        for group in variable_clusters:
            if len(group) == 1:
                # 単一ブロック
                block = group[0]
                if block.structure is not None:
                    group_structures.append(block.structure)
                else:
                    # シングルトン
                    idx = nfa_to_index[id(block.cluster[0])]
                    group_structures.append(idx)
            else:
                # 複数ブロックは推定状態数でソート+左重心
                sorted_group = sorted(group, key=lambda b: b.estimated_states)
                structures = []
                for block in sorted_group:
                    if block.structure is not None:
                        structures.append(block.structure)
                    else:
                        idx = nfa_to_index[id(block.cluster[0])]
                        structures.append(idx)
                # 左重心構造を構築
                group_structures.append(
                    self._build_left_heavy_structure_from_structures(structures)
                )

        logger.debug(
            "Stage 4 (ordering): Built %d group structures", len(group_structures)
        )

        # 最終的にバランスド構造で結合
        if len(group_structures) == 1:
            return group_structures[0]

        return self._build_balanced_structure_from_structures(group_structures)

    @staticmethod
    def _cluster_by_structure(spot_nfas: list[SpotNFA]) -> list[list[SpotNFA]]:  # noqa: C901
        """Cluster using hash-based pre-filtering + exact structural equality.

        Time complexity: O(n) average, O(n²) worst case (but rare)
        Space complexity: O(n)

        This is the most practical approach:
        1. First group by structural hash (O(n))
        2. Within each hash group, verify with is_structurally_equal
                (O(k²) where k << n)

        Args:
            spot_nfas: List of SpotNFA instances with formula_data

        Returns:
            List of clusters, where each cluster contains structurally similar NFAs

        """
        # Phase 1: ハッシュベースの粗いグループ化 O(n)
        hash_groups: dict[tuple, list[SpotNFA]] = defaultdict(list)

        for nfa in spot_nfas:
            if nfa.formula_data is None:
                hash_groups[(None,)].append(nfa)
                continue

            fd = nfa.formula_data
            # 構造ハッシュ。変数は考慮しないため、__hash__は使わない
            structure_hash = (
                fd.formula_type,
                fd.const,
                len(fd.coeffs),
                tuple(sorted(fd.coeffs.values())),
            )
            hash_groups[structure_hash].append(nfa)

        # Phase 2: 各ハッシュグループ内で厳密にチェック O(k²) per group
        final_clusters: list[list[SpotNFA]] = []

        for hash_group in hash_groups.values():
            if len(hash_group) == 1:
                # 1つしかない場合はそのまま追加
                final_clusters.append(hash_group)
                continue

            # このハッシュグループ内でさらに分割
            visited = [False] * len(hash_group)

            for i in range(len(hash_group)):
                if visited[i]:
                    continue

                # 新しいクラスタを作成
                cluster = [hash_group[i]]
                visited[i] = True

                # 残りの要素と比較
                formula_data_i = hash_group[i].formula_data
                if formula_data_i is not None:
                    for j in range(i + 1, len(hash_group)):
                        if visited[j]:
                            continue

                        formula_data_j = hash_group[j].formula_data
                        if (
                            formula_data_j is not None
                            and formula_data_i.is_structurally_equal(formula_data_j)
                        ):
                            cluster.append(hash_group[j])
                            visited[j] = True

                final_clusters.append(cluster)

        return final_clusters

    @staticmethod
    def _cluster_blocks_by_common_variables(
        blocks, min_common_vars: int = 1
    ) -> list[list]:
        """Cluster blocks by common variables using greedy strategy.

        Args:
            blocks: List of ClusterBlock instances
            min_common_vars: Minimum common variables to group

        Returns:
            List of block clusters

        """
        if not blocks:
            return []

        if len(blocks) == 1:
            return [blocks]

        # 各ブロックの変数集合
        var_sets = [block.variables for block in blocks]

        # 変数数でソート
        sorted_indices = sorted(
            range(len(blocks)), key=lambda i: len(var_sets[i]), reverse=True
        )

        clusters: list[list[int]] = []  # インデックスのクラスタ
        cluster_vars: list[set[str]] = []  # 各クラスタの変数集合
        assigned = [False] * len(blocks)

        for idx in sorted_indices:
            if assigned[idx]:
                continue

            # 既存のクラスタで最も共通変数が多いものを探す
            best_cluster = -1
            max_common = 0

            for cluster_id, c_vars in enumerate(cluster_vars):
                common = len(var_sets[idx] & c_vars)
                if common >= min_common_vars and common > max_common:
                    max_common = common
                    best_cluster = cluster_id

            if best_cluster >= 0:
                clusters[best_cluster].append(idx)
                cluster_vars[best_cluster] |= var_sets[idx]
            else:
                clusters.append([idx])
                cluster_vars.append(var_sets[idx].copy())

            assigned[idx] = True

        # インデックスからブロックに変換
        result_clusters = [[blocks[idx] for idx in cluster] for cluster in clusters]

        # クラスタサイズの降順でソート
        result_clusters.sort(key=len, reverse=True)

        return result_clusters

    @staticmethod
    def _cluster_by_common_variables_greedy(
        spot_nfas: list[SpotNFA], min_common_vars: int = 1
    ) -> list[list[SpotNFA]]:
        """Cluster NFAs greedily by maximizing common variables in each cluster.

        Strategy: For each unassigned NFA, add it to the cluster with which
        it shares the most variables.

        Time complexity: O(n² * m) where m=avg variables
        Space complexity: O(n * m)

        Args:
            spot_nfas: List of SpotNFA instances
            min_common_vars: Minimum common variables to add to a cluster

        Returns:
            List of clusters optimized for variable overlap

        """
        if not spot_nfas:
            return []

        if len(spot_nfas) == 1:
            return [spot_nfas]

        # 各NFAの変数集合を取得
        var_sets = [nfa.get_registered_ap() for nfa in spot_nfas]

        # 共通変数数でNFAをソート。変数が多い順
        # より多くの変数を持つNFAから処理すると、良いクラスタの種になる
        sorted_indices = sorted(
            range(len(spot_nfas)), key=lambda i: len(var_sets[i]), reverse=True
        )

        clusters: list[list[int]] = []  # インデックスのクラスタ
        cluster_vars: list[set[str]] = []  # 各クラスタの変数集合
        assigned = [False] * len(spot_nfas)

        for idx in sorted_indices:
            if assigned[idx]:
                continue

            # 既存のクラスタで最も共通変数が多いものを探す
            best_cluster = -1
            max_common = 0

            for cluster_id, c_vars in enumerate(cluster_vars):
                common = len(var_sets[idx] & c_vars)
                if common >= min_common_vars and common > max_common:
                    max_common = common
                    best_cluster = cluster_id

            if best_cluster >= 0:
                # 既存のクラスタに追加
                clusters[best_cluster].append(idx)
                cluster_vars[best_cluster] |= var_sets[idx]
            else:
                # 新しいクラスタを作成
                clusters.append([idx])
                cluster_vars.append(var_sets[idx].copy())

            assigned[idx] = True

        # インデックスからSpotNFAに変換
        result_clusters = [[spot_nfas[idx] for idx in cluster] for cluster in clusters]

        # クラスタサイズの降順でソート
        result_clusters.sort(key=len, reverse=True)

        return result_clusters

    def _build_tournament_from_clusters(
        self,
        clusters: list[list[SpotNFA]],
        original_automata: list[SpotNFA],
    ) -> TournamentStructure:
        """Build tournament structure from clusters.

        Strategy:
        1. For each cluster with 3+ elements, build a sub-tournament
           ordered by state count (smallest first)
        2. Combine all cluster structures into a final tournament

        Args:
            clusters: List of NFA clusters
            original_automata: Original list to map indices

        Returns:
            TournamentStructure representing the computation order

        """
        # NFAからインデックスへのマッピング
        nfa_to_index = {id(nfa): i for i, nfa in enumerate(original_automata)}

        def build_for_cluster(cluster: list[SpotNFA]) -> TournamentStructure:
            """Build tournament structure for a single cluster.

            For clusters with 3+ elements, order by state count (ascending).
            """
            if len(cluster) == 1:
                return nfa_to_index[id(cluster[0])]

            if len(cluster) == 2:  # noqa: PLR2004
                idx1 = nfa_to_index[id(cluster[0])]
                idx2 = nfa_to_index[id(cluster[1])]
                return (idx1, idx2)

            # 3要素以上: 状態数でソートしてトーナメント構造を構築
            return self._build_tournament_by_state_count(cluster, nfa_to_index)

        # 各クラスタの構造を作成
        cluster_structures = [build_for_cluster(cluster) for cluster in clusters]

        if len(cluster_structures) == 1:
            return cluster_structures[0]

        # クラスタ間を balanced structure で結合
        return self._build_balanced_structure_from_structures(cluster_structures)

    def _build_tournament_by_state_count(
        self,
        cluster: list[SpotNFA],
        nfa_to_index: dict[int, int],
    ) -> TournamentStructure:
        """Build tournament structure ordered by automaton state count.

        Strategy: Pair automata with smallest state counts first.
        This minimizes intermediate automaton sizes during intersection.

        Example:
            cluster = [A(100), B(50), C(30), D(20)]
            sorted = [D(20), C(30), B(50), A(100)]
            tournament = (((D, C), B), A)
                         = ((20+30=~50, 50), 100)
                         = (~100, 100)

        Args:
            cluster: List of SpotNFA instances (3+ elements)
            nfa_to_index: Mapping from NFA id to index

        Returns:
            TournamentStructure with smallest automata paired first

        """
        # Step 1: クラスタ内のNFAを状態数でソート (昇順)
        sorted_cluster = sorted(cluster, key=lambda nfa: nfa.num_states())

        # Step 2: ソートされたNFAのインデックスリストを取得
        sorted_indices = [nfa_to_index[id(nfa)] for nfa in sorted_cluster]

        # Step 3 & 4: 左結合でトーナメント構造を構築して返す
        # 最小の2つをペアにし、その結果を次の要素とペアにしていく
        # 例: [0, 1, 2, 3] -> (((0, 1), 2), 3)
        return self._build_left_heavy_structure(sorted_indices)

    @staticmethod
    def _build_left_heavy_structure(indices: list[int]) -> TournamentStructure:
        """Build left-heavy tournament structure from sorted indices.

        This creates a structure where smaller elements are paired first,
        minimizing the size of intermediate results.

        Example:
            indices = [0, 1, 2, 3]
            result = (((0, 1), 2), 3)

        Args:
            indices: List of automaton indices, already sorted by some criteria

        Returns:
            Left-heavy TournamentStructure

        """
        # ベースケース: 1要素または2要素
        if len(indices) == 1:
            return indices[0]
        if len(indices) <= 2:  # noqa: PLR2004
            return (indices[0], indices[1])

        # 再帰ケース: 3要素以上
        # 最初の2要素をペアにして、残りと結合
        left = (indices[0], indices[1])
        if len(indices) <= 3:  # noqa: PLR2004
            return (left, indices[2])
        # 再帰的に構築
        right = FormulaAutomataBuilder._build_left_heavy_structure(indices[2:])
        return (left, right)

    @staticmethod
    def _build_left_heavy_structure_from_structures(
        structures: list[TournamentStructure],
    ) -> TournamentStructure:
        """Build left-heavy tournament structure from existing structures.

        Example:
            structures = [s1, s2, s3, s4]
            result = (((s1, s2), s3), s4)

        Args:
            structures: List of TournamentStructures

        Returns:
            Left-heavy TournamentStructure

        """
        if len(structures) == 1:
            return structures[0]
        if len(structures) <= 2:  # noqa: PLR2004
            return (structures[0], structures[1])

        # 最初の2つをペアにして、残りと結合
        left = (structures[0], structures[1])
        if len(structures) <= 3:  # noqa: PLR2004
            return (left, structures[2])
        # 再帰的に構築
        right = FormulaAutomataBuilder._build_left_heavy_structure_from_structures(
            structures[2:]
        )
        return (left, right)

    @staticmethod
    def _build_balanced_structure_from_indices(
        indices: list[int],
    ) -> TournamentStructure:
        """Build balanced tournament structure from a list of indices.

        Args:
            indices: List of automaton indices

        Returns:
            Balanced TournamentStructure

        """
        if len(indices) == 1:
            return indices[0]

        mid = len(indices) // 2
        left = FormulaAutomataBuilder._build_balanced_structure_from_indices(
            indices[:mid]
        )
        right = FormulaAutomataBuilder._build_balanced_structure_from_indices(
            indices[mid:]
        )

        return (left, right)

    @staticmethod
    def _build_balanced_structure_from_structures(
        structures: list[TournamentStructure],
    ) -> TournamentStructure:
        """Build balanced tournament structure from existing structures.

        Args:
            structures: List of TournamentStructures

        Returns:
            Balanced combined TournamentStructure

        """
        if len(structures) == 1:
            return structures[0]

        mid = len(structures) // 2
        left = FormulaAutomataBuilder._build_balanced_structure_from_structures(
            structures[:mid]
        )
        right = FormulaAutomataBuilder._build_balanced_structure_from_structures(
            structures[mid:]
        )

        return (left, right)


@dataclass
class ClusterBlock:
    """Represents a cluster as a single unit."""

    cluster: list[SpotNFA]
    variables: set[str]  # 変数の和集合
    estimated_states: int  # 推定状態数
    structure: TournamentStructure | None = None  # 内部構造


class QuantVarCollector(DagWalker):
    """A simple walker to collect quantifier variables from a formula."""

    def __init__(self) -> None:
        super().__init__()
        self.quantifier_vars: set[str] = set()

    def collect(self, formula: FNode) -> set[str]:
        """Collect quantifier variables from the given formula."""
        self.walk(formula)
        return self.quantifier_vars

    def walk_exists(self, formula: FNode, args, **kwargs) -> None:
        self.quantifier_vars.update(formula.quantifier_vars())

    @handles(
        op.SYMBOL,
        *op.BOOL_CONNECTIVES,
        *op.CONSTANTS,
        *op.RELATIONS,
        *op.IRA_OPERATORS,
    )
    def walk_others(self, formula: FNode, args, **kwargs) -> None:
        """Handle other formula types without collecting quantifier variables."""
        return
