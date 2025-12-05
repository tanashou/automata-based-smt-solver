import logging

import spot
from pysmt.fnode import FNode
from pysmt.logics import LIA, QF_LIA
from pysmt.oracles import get_logic
from pysmt.rewritings import nnf
from pysmt.shortcuts import And

from absmt.automata.spot_nfa import SpotNFA
from absmt.formula import FormulaDataExtractor
from absmt.formula.rewritings import (
    DNFConverter,
    DoubleNegationEliminator,
    NegationEliminator,
    QuantifierPreservingNNFizer,
    UniversalQFEliminator,
)
from absmt.formula.smtlib_reader import SMTLIBReader
from absmt.formula_automata_builder import FormulaAutomataBuilder
from absmt.sat_status import SatStatus

logger = logging.getLogger(__name__)


class Solver:
    def __init__(self) -> None:
        self._formulas: list[FNode] = []

        self._data_extractor = FormulaDataExtractor()
        self._sat_status = SatStatus.UNKNOWN

    def _rewrite(self, formula: FNode) -> FNode:
        nnf_formula = nnf(formula)
        logger.debug("After converting to NNF: %s", nnf_formula.serialize(threshold=20))
        negation_eliminated = NegationEliminator().eliminate(nnf_formula)
        logger.debug(
            "After eliminating negations: %s",
            negation_eliminated.serialize(threshold=20),
        )
        return negation_eliminated

    def _rewrite_lia(self, formula: FNode) -> FNode:
        nnf_like_formula = QuantifierPreservingNNFizer().convert(formula)
        eliminate_universal_qf = UniversalQFEliminator().eliminate(nnf_like_formula)
        result = DoubleNegationEliminator().eliminate(eliminate_universal_qf)
        logger.debug(
            "After converting to quantifier-preserving NNF: %s",
            result.serialize(threshold=20),
        )
        return result

    def add(self, formula: FNode) -> None:
        self._formulas.append(formula)

    def read_from_smtlib(self, source: str, *, is_file_path: bool = False) -> SatStatus:
        smt_reader = SMTLIBReader()
        sat_status, formula = smt_reader.from_smt_lib(source, is_file_path=is_file_path)
        self._sat_status = sat_status
        self.add(formula)
        return sat_status

    def clear(self) -> None:
        self._formulas.clear()
        self._sat_status = SatStatus.UNKNOWN

    def solve(self) -> SatStatus:
        if not self._formulas:
            msg = "No formulas to solve."
            raise ValueError(msg)
        target_formula = And(self._formulas)
        logic = get_logic(target_formula)
        if logic == QF_LIA:
            return self._solve_qf_lia(target_formula)
        if logic == LIA:
            return self._solve_lia(target_formula)
        msg = "Solver only supports LIA and QF_LIA logics."
        raise NotImplementedError(msg)

    def _solve_qf_lia(self, target_formula: FNode) -> SatStatus:
        formula_automata_builder = FormulaAutomataBuilder()
        rewritten_formula = self._rewrite(target_formula)
        conjunctions = DNFConverter().convert(rewritten_formula)
        if not conjunctions:
            msg = "DNF conversion resulted in no conjunctions."
            raise RuntimeError(msg)

        for conjunction in conjunctions:
            result_nfa = formula_automata_builder.build(conjunction)

            # If result_nfa is None, the intersection is empty (continue to next)
            if result_nfa is None:
                continue

            if not result_nfa.is_empty() and self._is_infinite_language(result_nfa):
                if self._sat_status == SatStatus.UNSAT:
                    logger.error(
                        "The provided formulas are judged as satisfiable, "
                        "but the SMT-LIB status is 'unsat'."
                    )
                return SatStatus.SAT

        if self._sat_status == SatStatus.SAT:
            logger.error(
                "The provided formulas are judged as unsatisfiable, "
                "but the SMT-LIB status is 'sat'."
            )

        return SatStatus.UNSAT

    def _solve_lia(self, target_formula: FNode) -> SatStatus:
        """Solve the added formulas assuming they are in QF_LIA logic.

        This method is a convenience wrapper around `solve` and assumes
        that the added formulas are in the QF_LIA logic.
        """
        formula_automata_builder = FormulaAutomataBuilder()
        rewritten_formula = self._rewrite_lia(target_formula)

        result_nfa = formula_automata_builder.build(rewritten_formula)
        if result_nfa is None:
            return SatStatus.UNSAT
        if result_nfa.is_empty() or not self._is_infinite_language(result_nfa):
            if self._sat_status == SatStatus.SAT:
                logger.error(
                    "The provided formulas are judged as unsatisfiable, "
                    "but the SMT-LIB status is 'sat'."
                )
            return SatStatus.UNSAT
        if self._sat_status == SatStatus.UNSAT:
            logger.error(
                "The provided formulas are judged as satisfiable, "
                "but the SMT-LIB status is 'unsat'."
            )
        return SatStatus.SAT

    def _is_infinite_language(self, nfa: SpotNFA) -> bool:
        """Check if the automaton accepts an infinite words (padding invariant).

        We look for a non-trivial SCC that is NOT accepting.
        - The 'Accepting Sink' loop is accepting, representing the end of a finite word.
        - A 'Prefix' loop (padding) is NOT accepting (in our Universe construction).

        Therefore, if we find a loop that is not accepting, it implies we can
        pad the word infinitely, meaning the solution is valid in LIA.
        """
        aut = nfa.twa_graph
        scc_info = spot.scc_info(aut)

        for i in range(scc_info.scc_count()):
            # ループを持たない、自明なSCCは無視
            if scc_info.is_trivial(i):
                continue

            # そのループが受理条件を持っていないか確認
            # プレフィックス部分のループは受理条件を持たず、
            # 最後のSinkループだけが受理条件を持つ。
            if not scc_info.is_accepting_scc(i):
                return True

        return False
