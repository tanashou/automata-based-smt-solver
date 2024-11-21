# ruff: noqa: ANN201, ANN204, ANN001, ANN003, ARG002, D101, D107, D102
from pysmt.shortcuts import GT, LT, Or
from pysmt.walkers import IdentityDagWalker


class NeqConverter(IdentityDagWalker):
    def __init__(self):
        super().__init__()

    def walk_not(self, formula, args, **kwargs):
        # CNF に変換後に実行されるので、not は単一リテラルにのみ現れる。len(args) == 1
        if args[0].is_equals():
            lhs, rhs = args[0].args()
            return Or(LT(lhs, rhs), GT(lhs, rhs))
        return formula
