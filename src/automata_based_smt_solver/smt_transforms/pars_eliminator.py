# ruff: noqa: ANN201, ANN204, ANN001, ANN003, ARG002, D101, D107, D102
from pysmt.fnode import FNode
from pysmt.shortcuts import Int, Minus, Plus, Times
from pysmt.walkers import IdentityDagWalker


class ParsEliminator(IdentityDagWalker):
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
            flat_args.insert(0, Int(int_sum))
        if len(flat_args) == 1:
            return flat_args[0]
        return Plus(flat_args)

    def walk_times(self, formula: FNode, args: list[FNode], **_kwargs: object) -> FNode:
        if len(args) == self.MINUS_ARITY:
            left, right = args
            if right.is_plus():
                distributed = []
                for term in right.args():
                    if left.is_int_constant() and term.is_int_constant():
                        distributed.append(
                            Int(left.constant_value() * term.constant_value())
                        )
                    else:
                        distributed.append(Times([left, term]))
                return Plus(distributed)
            if left.is_plus():
                distributed = []
                for term in left.args():
                    if right.is_int_constant() and term.is_int_constant():
                        distributed.append(
                            Int(right.constant_value() * term.constant_value())
                        )
                    else:
                        distributed.append(Times([term, right]))
                return Plus(distributed)
        flat_args, int_prod, has_int = self._flatten_times_args(args)
        if has_int:
            flat_args.insert(0, Int(int_prod))
        if len(flat_args) == 1:
            return flat_args[0]
        return Times(flat_args)

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
        if len(args) == self.MINUS_ARITY:
            left, right = args
            if right.is_plus():
                # x - (y + z) = x - y - z
                result = Minus(left, right.args()[0])
                for term in right.args()[1:]:
                    result = Minus(result, term)
                # Recursively simplify in case of nested constants
                return self.walk_minus(result, [result.arg(0), result.arg(1)])
            if left.is_plus():
                # (x + y) - z = x + y - z
                return Minus(Plus(left.args()), right)
            if left.is_int_constant() and right.is_int_constant():
                return Int(left.constant_value() - right.constant_value())
            return Minus(left, right)
        # For n-ary minus, chain as left-associative: a-b-c-d = ((a-b)-c)-d
        result = args[0]
        for arg in args[1:]:
            result = Minus(result, arg)
        return result

    def walk_par(self, _formula: FNode, args: list[FNode], **_kwargs: object) -> FNode:
        if len(args) != 1:
            msg = "Par node should have exactly one child"
            raise ValueError(msg)
        return args[0]

    def walk_default(
        self, formula: FNode, args: list[FNode], **kwargs: object
    ) -> FNode:
        return formula.__class__(*args)
