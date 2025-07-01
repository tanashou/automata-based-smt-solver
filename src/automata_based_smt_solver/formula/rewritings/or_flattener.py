# ruff: noqa: ANN204, ARG002
from pysmt.fnode import FNode
from pysmt.shortcuts import Or
from pysmt.walkers import IdentityDagWalker


class OrFlattener(IdentityDagWalker):
    def __init__(self):
        super().__init__()

    def walk_or(self, formula: FNode, args: list[FNode], **_kwargs: object) -> FNode:
        literals = []
        for arg in args:
            if arg.is_or():
                literals.extend(arg.args())
            else:
                literals.append(arg)

        return Or(literals)
