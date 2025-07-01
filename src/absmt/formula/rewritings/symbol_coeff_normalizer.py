# ruff: noqa: ANN201, ANN001, ANN003, ARG002

from pysmt.shortcuts import Int, Times
from pysmt.typing import BOOL
from pysmt.walkers import IdentityDagWalker


class SymbolCoeffNormalizer(IdentityDagWalker):
    def __init__(self) -> None:
        super().__init__()

    def walk_symbol(self, formula, args, **kwargs):
        if formula.get_type() == BOOL:
            return formula
        return Times(Int(1), formula)
