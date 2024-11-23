from pysmt.fnode import FNode
from pysmt.rewritings import CNFizer

from automata_based_smt_solver.formula_rewite_walker import FormulaRewriteWalker


class FormulaRewriter:
    def __init__(self) -> None:
        self.cnfizer = CNFizer()
        self.walker = FormulaRewriteWalker()

    def rewrite(self, formula: FNode) -> FNode:
        cnf = self.cnfizer.convert_as_formula(formula)
        return self.walker.walk(cnf)
