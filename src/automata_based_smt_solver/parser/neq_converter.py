# ruff: noqa: ANN201, ANN204, ANN001, ANN003, ARG002
from pysmt.walkers import DagWalker
from pysmt.shortcuts import GT, LT


class NeqConverter(DagWalker):
    def __init__(self):
        super().__init__()

    def walk_not_equals(self, formula, args, **kwargs):
        print("not equals")
        print(formula, args)
        return args
