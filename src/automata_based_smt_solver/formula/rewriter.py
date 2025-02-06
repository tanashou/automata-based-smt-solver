from pysmt.fnode import FNode
from pysmt.rewritings import CNFizer

from automata_based_smt_solver.formula.negation_eliminator import NegationEliminator


class Rewriter:
    def __init__(self) -> None:
        self.cnfizer = CNFizer()
        self.walker = NegationEliminator()

    def cnfize_and_rewrite(self, formula: FNode) -> FNode:
        cnf = self.cnfizer.convert_as_formula(formula)
        return self.walker.walk(cnf)
