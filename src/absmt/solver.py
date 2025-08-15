import logging

from pysmt.fnode import FNode
from pysmt.shortcuts import And
from pysmt.smtlib.parser import SmtLibParser

from absmt.formula import FormulaDataExtractor
from absmt.formula.formula_data_extractor import collect_literals_from_tree
from absmt.formula.rewritings import (
    DoubleNegationEliminator,
    NegationEliminator,
    QuantifierPreservingNNFizer,
    UniversalQFEliminator,
)
from absmt.formula.type import FormulaData
from absmt.formula_automata_builder import FormulaAutomataBuilder
from absmt.sat_status import SatStatus

logger = logging.getLogger(__name__)


class Solver:
    def __init__(self) -> None:
        self.parser = SmtLibParser()
        self._formulas: list[FNode] = []

        self._universal_qf_eliminator = UniversalQFEliminator()
        self._nnfizer = QuantifierPreservingNNFizer()
        self._double_negation_eliminator = DoubleNegationEliminator()
        self._negation_eliminator = NegationEliminator()

        self._data_extractor = FormulaDataExtractor()

    def _rewrite(self, formula: FNode) -> FNode:
        quantifier_rewritten = self._universal_qf_eliminator.walk(formula)
        nnf_formula = self._nnfizer.convert(quantifier_rewritten)
        double_negation_eliminated = self._double_negation_eliminator.walk(nnf_formula)
        return self._negation_eliminator.walk(double_negation_eliminated)

    def _extract_data(
        self, preprocessed_formula: FNode
    ) -> tuple[object, list[FormulaData]]:
        formula_tree = self._data_extractor.extract_data(preprocessed_formula)
        literals_data = collect_literals_from_tree(formula_tree)
        return formula_tree, literals_data

    def add(self, formula: FNode) -> None:
        self._formulas.append(formula)

    def clear(self) -> None:
        self._formulas.clear()

    def solve(self) -> SatStatus:
        if not self._formulas:
            msg = "No formulas to solve."
            raise ValueError(msg)

        formula_automata_builder = FormulaAutomataBuilder()

        target_formula = And(self._formulas)
        logger.debug("Solving formula: %s", target_formula.serialize(threshold=100))
        rewritten_formula = self._rewrite(target_formula)
        result_nfa = formula_automata_builder.build(rewritten_formula)

        if result_nfa.is_empty():
            logger.debug("Formula is UNSAT.")
            return SatStatus.UNSAT

        logger.debug("Formula is SAT.")
        return SatStatus.SAT
