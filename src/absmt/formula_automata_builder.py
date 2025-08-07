from pysmt.fnode import FNode
from pysmt.walkers import DagWalker

from absmt.automata.nfa import NFA


class FormulaAutomataBuilder(DagWalker):
    def __init__(self) -> None:
        super().__init__(invalidate_memoization=True)

    def build(self, formula: FNode) -> NFA:
        return self.walk(formula)

    # TODO: Implement walker methods
