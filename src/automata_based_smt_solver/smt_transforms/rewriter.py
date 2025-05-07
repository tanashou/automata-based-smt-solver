from pysmt.fnode import FNode
from pysmt.rewritings import CNFizer

from automata_based_smt_solver.smt_transforms.minus_eliminator import MinusEliminator
from automata_based_smt_solver.smt_transforms.negation_eliminator import (
    NegationEliminator,
)


class Rewriter:
    def __init__(self) -> None:
        self.cnfizer = CNFizer()
        self.negation_eliminator = NegationEliminator()
        self.minus_eliminator = MinusEliminator()

    def cnfize_and_rewrite(self, formula: FNode) -> FNode:
        cnf = self.cnfizer.convert_as_formula(formula)
        # ドキュメントにwalker を一括で扱うクラスがあった。
        negation_eliminated_cnf = self.negation_eliminator.walk(cnf)
        return self.minus_eliminator.walk(negation_eliminated_cnf)
