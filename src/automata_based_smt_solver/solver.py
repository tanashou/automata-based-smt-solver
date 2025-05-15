import pysmt.rewritings
from pysmt.fnode import FNode
from pysmt.rewritings import TimesDistributor
from pysmt.smtlib.parser import SmtLibParser

from automata_based_smt_solver.smt_transforms.calculating_bracket_expander import (
    CalculatingBracketExpander,
)
from automata_based_smt_solver.smt_transforms.formula_data_extractor import (
    FormulaData,
    FormulaDataExtractor,
)
from automata_based_smt_solver.smt_transforms.negation_eliminator import (
    NegationEliminator,
)
from automata_based_smt_solver.smt_transforms.smtlib_reader import SMTLIBReader


class Solver:
    def __init__(self) -> None:
        self.parser = SmtLibParser()
        self.reader = SMTLIBReader()

    def _rewrite_formula(self, formula: FNode) -> FNode:
        cnf = pysmt.rewritings.cnf(formula)
        negation_eliminated_cnf = NegationEliminator().walk(cnf)
        distributed = TimesDistributor().walk(negation_eliminated_cnf)
        return CalculatingBracketExpander().walk(distributed)

    def _extract_data(self, cnf: FNode) -> list[list[FormulaData]]:
        result = []
        data_extractor = FormulaDataExtractor()
        for clause in cnf.args():
            literals = [data_extractor.extract(literal) for literal in clause.args()]
            result.append(literals)

        return result
