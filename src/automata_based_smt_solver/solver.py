import pysmt.rewritings
from pysmt.fnode import FNode
from pysmt.rewritings import TimesDistributor
from pysmt.shortcuts import And
from pysmt.smtlib.parser import SmtLibParser

from automata_based_smt_solver.automata_builder import AutomataBuilder
from automata_based_smt_solver.formula import DataExtractor
from automata_based_smt_solver.formula.rewritings import (
    CalculatingBracketExpander,
    NegationEliminator,
    OrFlattener,
    SymbolCoeffNormalizer,
)
from automata_based_smt_solver.formula.type import FormulaData
from automata_based_smt_solver.sat_status import SatStatus


class Solver:
    def __init__(self) -> None:
        self.parser = SmtLibParser()
        self._formulas: list[FNode] = []

    def _rewrite_formula(self, formula: FNode) -> FNode:
        cnf = pysmt.rewritings.cnf(formula)
        negation_eliminated_cnf = NegationEliminator().walk(cnf)
        flattened_cnf = OrFlattener().walk(negation_eliminated_cnf)
        distributed = TimesDistributor().walk(flattened_cnf)
        normalized_coeff = SymbolCoeffNormalizer().walk(distributed)
        return CalculatingBracketExpander().walk(normalized_coeff)

    def _extract_data(self, cnf: FNode) -> list[list[FormulaData]]:
        result = []
        data_extractor = DataExtractor()
        if cnf.is_and():
            for clause in cnf.args():
                if clause.is_or():
                    literals = [
                        data_extractor.extract(literal) for literal in clause.args()
                    ]
                    result.append(literals)
                else:
                    literal = data_extractor.extract(clause)
                    result.append([literal])
        elif cnf.is_or():
            literals = [data_extractor.extract(literal) for literal in cnf.args()]
            result.append(literals)
        else:
            literal = data_extractor.extract(cnf)
            result.append([literal])

        return result

    def add(self, formula: FNode) -> None:
        self._formulas.append(formula)

    def solve(self) -> SatStatus:
        if not self._formulas:
            msg = "No formulas to solve."
            raise ValueError(msg)

        formula = And(self._formulas).simplify()
        cnf = self._rewrite_formula(formula)
        cnf_data = self._extract_data(cnf)

        variables: list[FNode] = sorted(cnf.get_free_variables(), key=lambda v: str(v))
        var_index_map = {name: index for index, name in enumerate(variables)}

        for clause_data in cnf_data:
            for literal_data in clause_data:
                builder = AutomataBuilder(
                    literal_data,
                    variables,
                    var_index_map,
                )
                builder.build_step()

        return SatStatus.UNKNOWN
