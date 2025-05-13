# ruff: noqa: ANN201, ANN204, ANN001, ANN003, ARG002, D101, D107, D102
from pysmt.fnode import FNode
from pysmt.shortcuts import Int, Plus, Times
from pysmt.walkers import IdentityDagWalker


# need to use after pysmt.rewriter.TimesDistributor . This also rewrites minus as plus
class CalculatingBracketExpander(IdentityDagWalker):
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
        # Flatten nested Times and multiply all integer constants.
        # Only 1 nested Times is allowed. TimesDistributor removes all nested Times.
        flat_args = []
        int_prod = 1

        for arg in args:
            if arg.is_times():
                for sub_arg in arg.args():
                    if sub_arg.is_int_constant():
                        int_prod *= sub_arg.constant_value()
                    else:
                        flat_args.append(sub_arg)
            elif arg.is_int_constant():
                int_prod *= arg.constant_value()
            else:
                flat_args.append(arg)

        if int_prod == 0:
            return Int(0)
        # Only include the constant if it's not 1, or if there are no other args
        if int_prod != 1 or not flat_args:
            flat_args = [Int(int_prod), *flat_args]
        if len(flat_args) == 1:
            return flat_args[0]
        return Times(flat_args)
