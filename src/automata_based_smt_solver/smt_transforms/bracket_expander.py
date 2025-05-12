# ruff: noqa: ANN201, ANN204, ANN001, ANN003, ARG002, D101, D107, D102
from pysmt.fnode import FNode
from pysmt.shortcuts import Int, Plus, Times
from pysmt.walkers import IdentityDagWalker


class BracketExpander(IdentityDagWalker):
    def __init__(self) -> None:
        super().__init__()

    def walk_plus(self, formula: FNode, args: list[FNode], **_kwargs: object) -> FNode:
        flat_args = []
        int_sum = 0
        for arg in args:
            if arg.is_plus():
                flat_args.extend(arg.args())
            elif arg.is_int_constant():
                int_sum += arg.constant_value()
            else:
                flat_args.append(arg)
        if int_sum != 0:
            flat_args.append(Int(int_sum))
        if len(flat_args) == 1:
            # result is an integer or a symbol
            return flat_args[0]
        return Plus(flat_args)

    def walk_times(self, formula: FNode, args: list[FNode], **_kwargs: object) -> FNode:
        flat_args = []
        int_prod = 1

        # 内側の括弧はすでに展開されているかも
        for arg in args:
            if arg.is_int_constant():
                int_prod *= arg.constant_value()
            else:
                flat_args.append(arg)

        if int_prod != 1:
            flat_args.append(Int(int_prod))
        if len(flat_args) == 1:
            # result is an integer or a symbol
            return flat_args[0]

        # Distribute multiplication over addition if any argument is a Plus node
        for i, arg in enumerate(flat_args):
            if arg.is_plus():
                # Distribute Times over Plus: a * (b + c) => a*b + a*c
                others = flat_args[:i] + flat_args[i + 1 :]
                distributed = [
                    self.walk_times(formula, [term, *others]) for term in arg.args()
                ]
                return self.walk_plus(Plus(distributed), distributed)

        # Flatten nested Times and combine integer constants
        flat_args, int_prod = self._flatten_times_args(flat_args)
        if int_prod != 1:
            flat_args.append(Int(int_prod))
        if len(flat_args) == 1:
            return flat_args[0]
        return Times(flat_args)

    def _flatten_times_args(self, args: list[FNode]) -> tuple[list[FNode], int]:
        flat_args = []
        int_prod = 1
        for arg in args:
            if arg.is_times():
                for sub in arg.args():
                    if sub.is_int_constant():
                        int_prod *= sub.constant_value()
                    else:
                        flat_args.append(sub)
            elif arg.is_int_constant():
                int_prod *= arg.constant_value()
            else:
                flat_args.append(arg)
        return flat_args, int_prod

    def walk_minus(self, formula: FNode, args: list[FNode], **_kwargs: object) -> FNode:
        # args length is guaranteed to be 2
        left, right = args

        negated_right = Times(Int(-1), right)
        negated_right_expanded = self.walk_times(
            negated_right, list(negated_right.args())
        )
        sum_expr = Plus(left, negated_right_expanded)
        return self.walk_plus(sum_expr, list(sum_expr.args()))
