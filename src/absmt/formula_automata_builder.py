# ruff: noqa: ANN001, ANN003, ARG002

import logging
from collections import defaultdict

import pysmt.operators as op
import spot
from pysmt.fnode import FNode
from pysmt.walkers import DagWalker
from pysmt.walkers.generic import handles

from absmt.automata.spot_nfa import SpotNFA, TournamentStructure
from absmt.automata_builder import AutomataBuilder
from absmt.formula import LiteralDataExtractor

logger = logging.getLogger(__name__)


class FormulaAutomataBuilder(DagWalker):
    def __init__(self) -> None:
        super().__init__()
        self._literal_data_extractor = LiteralDataExtractor()
        self._bdict = spot.make_bdd_dict()

    def build(self, formula: FNode) -> SpotNFA | None:
        all_vars = [str(var) for var in formula.get_free_variables()]
        all_var_index_map = {var: index for index, var in enumerate(all_vars)}
        walk_context = {
            "all_vars": all_vars,
            "all_var_index_map": all_var_index_map,
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

        res = SpotNFA.intersect_all(*args)

        if res is None:
            logger.debug("Complete building for 'and': result is empty (None).")
        else:
            logger.debug("Complete building for 'and'.")

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
        formula_str = formula.serialize(threshold=20)
        logger.debug(
            "Prepared automaton for 'literal'; formula=%s",
            formula_str,
        )

        return res

    @handles(
        op.SYMBOL,
        *op.CONSTANTS,
        *op.IRA_OPERATORS,
    )
    def walk_others(self, formula: FNode, args, **kwargs) -> None:
        return

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

    def _create_tournament_structure(
        self, automata: list[SpotNFA]
    ) -> TournamentStructure:
        """Create tournament structure with two-stage clustering.

        Stage 1: Cluster by structural similarity (formula_data)
        Stage 2: Cluster singleton groups by common variables

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

        # Stage 2: サイズ1のクラスタを共通変数でクラスタリング
        final_clusters: list[list[SpotNFA]] = []
        singletons: list[SpotNFA] = []

        for cluster in structure_clusters:
            if len(cluster) == 1:
                singletons.extend(cluster)
            else:
                final_clusters.append(cluster)

        if singletons:
            # シングルトンを共通変数でクラスタリング
            variable_clusters = self._cluster_by_common_variables_greedy(
                singletons, min_common_vars=1
            )
            final_clusters.extend(variable_clusters)

            logger.debug(
                "Stage 2 (variables): %d singletons -> %d clusters",
                len(singletons),
                len(variable_clusters),
            )

        logger.debug(
            "Final: %d NFAs -> %d clusters", len(automata), len(final_clusters)
        )

        # クラスタからTournamentStructureを構築
        return self._build_tournament_from_clusters(final_clusters, automata)

    def _build_tournament_from_clusters(
        self,
        clusters: list[list[SpotNFA]],
        original_automata: list[SpotNFA],
    ) -> TournamentStructure: ...
