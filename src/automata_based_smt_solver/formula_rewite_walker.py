# ruff: noqa: ANN201, ANN204, ANN001, ANN003, ARG002, D101, D107, D102, ANN101
from pysmt.fnode import FNode
from pysmt.shortcuts import GE, GT, LT, Equals, Int, Or
from pysmt.walkers import IdentityDagWalker


# neq の変換、式の整形(定数が右辺か左辺のみに現れる)を行う
class FormulaRewriteWalker(IdentityDagWalker):
    def __init__(self):
        super().__init__()

    def walk_not(self, formula, args, **kwargs):
        # CNF に変換後に実行されるので、not は単一リテラルにのみ現れる。
        if len(args) != 1:
            msg = "'not' should have exactly one argument"
            raise ValueError(msg)

        subformula = args[0]
        if subformula.is_equals():
            lhs, rhs = subformula.args()
            return Or(LT(lhs, rhs), GT(lhs, rhs))
        return formula

    def _rewrite_inequality(self, args) -> tuple[FNode, int]:
        lhs, rhs = args
        combined = lhs - rhs
        left_terms, right_terms = [], []
        for arg in combined.args():
            if arg.is_constant():
                right_terms.append(arg)
            else:
                left_terms.append(arg)

        # sum を使うと + 0 が追加されてしまう
        new_lhs = None
        for term in left_terms:
            new_lhs = term if new_lhs is None else new_lhs + term
        new_rhs = sum(term.constant_value() for term in right_terms)

        if new_lhs is None:
            msg = "new_lhs should not be None"
            raise ValueError(msg)
        return new_lhs, new_rhs

    def walk_equals(self, formula, args, **kwargs):
        lhs, rhs = self._rewrite_inequality(args)
        return Equals(lhs, Int(rhs))

    def walk_lt(self, formula, args, **kwargs):
        lhs, rhs = self._rewrite_inequality(args)
        return LT(lhs, Int(rhs))

    def walk_ge(self, formula, args, **kwargs):
        lhs, rhs = self._rewrite_inequality(args)
        return GE(lhs, Int(rhs))

    def walk_gt(self, formula, args, **kwargs):
        lhs, rhs = self._rewrite_inequality(args)
        return GT(lhs, Int(rhs))
