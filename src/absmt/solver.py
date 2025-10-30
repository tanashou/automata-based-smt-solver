import logging

from pysmt.fnode import FNode
from pysmt.rewritings import nnf
from pysmt.shortcuts import And

from absmt.formula import FormulaDataExtractor
from absmt.formula.rewritings import (
    DNFGenerator,
    DoubleNegationEliminator,
    NegationEliminator,
)
from absmt.formula.smtlib_reader import SMTLIBReader
from absmt.formula_automata_builder import FormulaAutomataBuilder
from absmt.sat_status import SatStatus

logger = logging.getLogger(__name__)


class Solver:
    def __init__(self) -> None:
        self._formulas: list[FNode] = []

        self._double_negation_eliminator = DoubleNegationEliminator()
        self._negation_eliminator = NegationEliminator()
        self._dnf_generator = DNFGenerator()
        self._data_extractor = FormulaDataExtractor()
        self._sat_status = SatStatus.UNKNOWN

    def _rewrite(self, formula: FNode) -> FNode:
        nnf_formula = nnf(formula)
        logger.debug("After converting to NNF: %s", nnf_formula.serialize(threshold=20))
        negation_eliminated = self._negation_eliminator.walk(nnf_formula)
        logger.debug(
            "After eliminating negations: %s",
            negation_eliminated.serialize(threshold=20),
        )
        return negation_eliminated

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

        formula_automata_builder = FormulaAutomataBuilder()

        target_formula = And(self._formulas)
        rewritten_formula = self._rewrite(target_formula)
        conjunctions = self._dnf_generator.get_conjunctions(rewritten_formula)
        for conjunction in conjunctions:
            result_nfa = formula_automata_builder.build(conjunction)

            if not result_nfa.is_empty():
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
