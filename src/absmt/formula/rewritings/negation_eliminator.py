# ruff: noqa: ANN201, ANN204, ANN001, ANN003, ARG002
from typing import ClassVar

from pysmt.logics import LIA, QF_LIA
from pysmt.oracles import get_logic
from pysmt.shortcuts import GE, GT, LT, Or
from pysmt.walkers import IdentityDagWalker


# neq の変換、式の整形(定数が右辺か左辺のみに現れる)を行う
class NegationEliminator(IdentityDagWalker):
    """Eliminates negation operators from a CNF formula.

    This walker rewrites 'not' expressions into equivalent forms except for negations
    applied directly to Boolean variables.
    For example, it transforms 'not(a = b)' into '(a < b or a > b)' and
    'not(a < b)' into '(a >= b)'.
    It is intended for use after converting a formula to conjunctive normal form.
    """

    LOGICS: ClassVar[list] = [QF_LIA, LIA]

    def __init__(self):
        super().__init__()

    def eliminate(self, formula):
        self.logic = get_logic(formula)
        return self.walk(formula)

    def walk_not(self, formula, args, **kwargs):
        if len(args) != 1:
            msg = "NegationEliminator is intended for use after NNF conversion."
            raise ValueError(msg)

        subformula = args[0]
        # pysmtの仕様より、equals, lt, le しか現れない
        # QF_LIA だけ equals を LT or GT に変換する
        if subformula.is_equals() and self.logic <= QF_LIA:
            lhs, rhs = subformula.args()
            return Or(LT(lhs, rhs), GT(lhs, rhs))
        if subformula.is_lt():
            lhs, rhs = subformula.args()
            return GE(lhs, rhs)
        if subformula.is_le():
            lhs, rhs = subformula.args()
            return GT(lhs, rhs)
        return formula
