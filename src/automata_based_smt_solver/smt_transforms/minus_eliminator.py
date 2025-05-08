# ruff: noqa: ANN201, ANN204, ANN001, ANN003, ARG002, D101, D107, D102
from pysmt.shortcuts import Int, Plus, Times
from pysmt.walkers import IdentityDagWalker


# Transforms a binary minus operator into an addition.
# For example:
#   (x1 * 3) - x2       ->  (x1 * 3) + (-1 * x2)
#   (x1 * 3) - (x2 * 2)   ->  (x1 * 3) + (-2 * x2)
class MinusEliminator(IdentityDagWalker):
    def __init__(self):
        super().__init__()

    def walk_minus(self, formula, args, **kwargs):
        if len(args) != 2:  # noqa: PLR2004
            msg = "MinusEliminator expects a binary minus operator with 2 args."
            raise ValueError(msg)
        left, right = args

        # If the right side is a constant, directly negate it
        if right.is_constant():
            new_const = -right.constant_value()
            return Plus(left, Int(new_const))

        # If the right side is a TIMES node, try to push the minus into the constant.
        if right.is_times():
            a, b = right.args()
            if a.is_constant() and b.is_symbol():
                new_const = -a.constant_value()
                new_right = Times(Int(new_const), b)
                return Plus(left, new_right)
            if b.is_constant() and a.is_symbol():
                new_const = -b.constant_value()
                new_right = Times(a, Int(new_const))
                return Plus(left, new_right)
        # Otherwise, wrap the right side in a multiplication by -1.
        new_right = Times(Int(-1), right)
        return Plus(left, new_right)
