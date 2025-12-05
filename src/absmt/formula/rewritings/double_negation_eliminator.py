# ruff: noqa: ANN201, ANN001, ANN003, ARG002
from pysmt.shortcuts import Not
from pysmt.walkers import IdentityDagWalker


class DoubleNegationEliminator(IdentityDagWalker):
    """A walker that simplifies double negations (e.g., Not(Not(A))) into A.

    This walker identifies the pattern 'Not(Not(...))' and replaces it with
    the innermost expression. For other 'Not' expressions, it reconstructs
    them as they are.
    """

    def __init__(self) -> None:
        super().__init__()

    def eliminate(self, formula):
        return self.walk(formula)

    def walk_not(self, formula, args, **kwargs):
        # args[0] is the result of walking the child of the current NOT node.
        rewritten_child = args[0]

        # Check if the rewritten child is itself a NOT node.
        # This identifies the pattern Not(Not(A)).
        if rewritten_child.is_not():
            # The result is the content of the inner NOT,
            # effectively removing both negations.
            # rewritten_child is Not(A'), so its argument is A'.
            return rewritten_child.arg(0)

        # If the child is not a NOT node, reconstruct the negation
        # around the (potentially rewritten) child.
        return Not(rewritten_child)
