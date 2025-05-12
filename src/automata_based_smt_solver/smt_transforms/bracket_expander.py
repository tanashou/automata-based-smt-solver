# ruff: noqa: ANN201, ANN204, ANN001, ANN003, ARG002, D101, D107, D102
from pysmt.fnode import FNode
from pysmt.shortcuts import Int, Plus, Times
from pysmt.walkers import IdentityDagWalker


class BracketExpander(IdentityDagWalker):
    MINUS_ARITY = 2

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
            # result is an integer
            return flat_args[0]
        return Plus(flat_args)

    def walk_times(self, formula: FNode, args: list[FNode], **_kwargs: object) -> FNode:
        pass

    def _flatten_times_args(self, args: list[FNode]) -> tuple[list[FNode], int, bool]:
        flat_args = []
        int_prod = 1
        has_int = False
        for arg in args:
            if arg.is_times():
                for sub in arg.args():
                    if sub.is_int_constant():
                        int_prod *= sub.constant_value()
                        has_int = True
                    else:
                        flat_args.append(sub)
            elif arg.is_int_constant():
                int_prod *= arg.constant_value()
                has_int = True
            else:
                flat_args.append(arg)
        return flat_args, int_prod, has_int

    def walk_minus(self, formula: FNode, args: list[FNode], **_kwargs: object) -> FNode:
        # args length is guaranteed to be 2
        minuend, subtrahend = args

        term = Times(Int(-1), subtrahend)
        rewritten_term = self.walk_times(term, list(term.args()))
        return Plus(minuend, rewritten_term)

    def walk_par(self, _formula: FNode, args: list[FNode], **_kwargs: object) -> FNode:
        if len(args) != 1:
            msg = "Par node should have exactly one child"
            raise ValueError(msg)
        return args[0]

    def walk_default(
        self, formula: FNode, args: list[FNode], **kwargs: object
    ) -> FNode:
        return formula.__class__(*args)
