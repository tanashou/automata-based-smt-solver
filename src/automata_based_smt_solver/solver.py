from pysmt.fnode import FNode
from pysmt.rewritings import CNFizer

from automata_based_smt_solver.smt_transforms.bracket_expander import BracketExpander
from automata_based_smt_solver.smt_transforms.formula_data_extractor import (
    FormulaData,
    FormulaDataExtractor,
)
from automata_based_smt_solver.smt_transforms.negation_eliminator import (
    NegationEliminator,
)


class Solver:
    def _cnfize_and_eliminate_minus_negation(self, formula: FNode) -> FNode:
        cnf = CNFizer().convert_as_formula(formula)
        negation_eliminated_cnf = NegationEliminator().walk(cnf)
        return BracketExpander().walk(negation_eliminated_cnf)

    def _extract_data(self, cnf: FNode) -> list[list[FormulaData]]:
        result = []
        data_extractor = FormulaDataExtractor()
        for clause in cnf:
            literals = [data_extractor.extract(literal) for literal in clause]
            result.append(literals)

        return result
