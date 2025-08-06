import logging

from pysmt.fnode import FNode
from pysmt.shortcuts import And
from pysmt.smtlib.parser import SmtLibParser

from absmt.automata.nfa import NFA
from absmt.automata_builder import AutomataBuilder
from absmt.formula import FormulaDataExtractor
from absmt.formula.formula_data_extractor import collect_literals_from_tree
from absmt.formula.rewritings import (
    DoubleNegationEliminator,
    NegationEliminator,
    QuantifierPreservingNNFizer,
    UniversalQFEliminator,
)
from absmt.formula.type import FormulaData
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

    def _setup_and_build(
        self,
        conjunction_data: list[FormulaData],
        all_vars: list[str],
        var_index_map: dict[str, int],
    ) -> list[AutomataBuilder]:
        builders: list[AutomataBuilder] = []
        for literal_data in conjunction_data:
            used_vars = list(literal_data.coeffs.keys())
            builder = AutomataBuilder(
                literal_data,
                all_vars,
                var_index_map,
                used_vars,
            )
            builder.build()
            builders.append(builder)
        return builders

    def _intersect_all_nfa_(self, union_nfas: list[NFA]) -> NFA | None:
        if not union_nfas:
            return None
        all_nfa = union_nfas[0]
        for union_nfa in union_nfas[1:]:
            all_nfa = all_nfa.intersection(union_nfa)
        return all_nfa

    def solve(self) -> SatStatus:
        if not self._formulas:
            msg = "No formulas to solve."
            raise ValueError(msg)

        target_formula = And(self._formulas)
        logger.debug("Solving formula: %s", target_formula.serialize(threshold=100))
        target_formula_tree, literals_data = self._extract_data(target_formula)
        logger.debug("Rewritten formula to DNF.")

        # TODO: create a solver methodz

        return SatStatus.UNSAT
