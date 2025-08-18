# ruff: noqa: ANN001, ANN003
from pysmt.fnode import FNode
from pysmt.shortcuts import Exists, Not
from pysmt.walkers import IdentityDagWalker


class UniversalQFEliminator(IdentityDagWalker):
    """Eliminates forall operators and rewrite using exists.

    ドモルガンの法則を利用して、全称量化子を存在量化子に置き換える。
    """

    def __init__(self) -> None:
        super().__init__()

    def walk_forall(self, formula, args, **kwargs) -> FNode:
        """Rewrite forall to exists using De Morgan's laws.

        ∀x.φ(x) → ¬¬∀x.φ(x) → ¬∃x.(¬φ(x))
        """
        qvars = [self.walk_symbol(v, args, **kwargs) for v in formula.quantifier_vars()]
        inner_formula = args[0]
        return Not(Exists(qvars, Not(inner_formula)))
