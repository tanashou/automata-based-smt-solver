# ruff: noqa: ANN201, ANN001, ANN003, ARG002
from collections import defaultdict

from pysmt.exceptions import UnsupportedOperatorError
from pysmt.fnode import FNode
from pysmt.walkers import DagWalker

from absmt.formula.type import FormulaData, FormulaType, QuantifierType


class FormulaDataExtractor(DagWalker):
    def __init__(self) -> None:
        super().__init__(invalidate_memoization=True)

    def extract(self, formula) -> list[list[FormulaData]]:  # [] 内は and, [] 同士が or
        self._coeffs: defaultdict[str, int] = defaultdict(int)
        self._const: int = 0
        self._side_sign: int = 1

        if formula.is_equals():
            self._formula_type = FormulaType.EQ
        elif formula.is_le():
            self._formula_type = FormulaType.LE
        elif formula.is_lt():
            self._formula_type = FormulaType.LE
            self._const -= 1
        else:
            msg = "Unsupported formula type. Only EQ, LE, and LT are supported."
            raise UnsupportedOperatorError(msg)

        # 括弧展開済み、定数は右辺か左辺に単体として、または足し算、引き算にしか現れない
        lhs, rhs = formula.args()
        if lhs.is_int_constant():
            self._const -= lhs.constant_value()
        if rhs.is_int_constant():
            self._const += rhs.constant_value()

        self._side_sign = 1
        self.walk(lhs)
        self._side_sign = -1
        self.walk(rhs)

        final_coeffs = {k: v for k, v in self._coeffs.items() if v != 0}
        return FormulaData(
            QuantifierType.NONE,
            final_coeffs,
            self._const,
            self._formula_type,
            self._has_negation_before_bool_var,
        )

    # Walker methods

    def walk_not(self, formula, args, **kwargs):
        self._has_negation_before_bool_var = True
        return formula

    def walk_times(self, formula, args: list[FNode], **kwargs):
        expected_arg_count = 2
        if len(args) != expected_arg_count:
            # var with 2 or more degrees exists"
            msg = "TIMES operator must have exactly two arguments."
            raise UnsupportedOperatorError(msg)

        a, b = args
        if a.is_int_constant() and b.is_symbol():
            coeff = a.constant_value() * self._side_sign
            self._coeffs[str(b)] += coeff
        elif a.is_symbol() and b.is_int_constant():
            coeff = b.constant_value() * self._side_sign
            self._coeffs[str(a)] += coeff
        else:
            msg = "Multiplication of variables (var * var) is not allowed in LIA."
            raise UnsupportedOperatorError(msg)
        return formula

    def walk_plus(self, formula, args: list[FNode], **kwargs):
        for arg in args:
            if arg.is_int_constant():
                self._const += arg.constant_value() * (-self._side_sign)
        return formula

    def walk_minus(self, formula, args, **kwargs):
        # Minus is removed by pysmt.rewriter.TimesDistributor
        return formula

    def walk_and(self, formula, args, **kwargs):
        msg = (
            "Logical 'and' is not allowed. Please eliminate it before using this "
            "extractor."
        )
        raise UnsupportedOperatorError(msg)

    def walk_or(self, formula, args, **kwargs):
        msg = (
            "Logical 'or' is not allowed. Please eliminate it before using this "
            "extractor."
        )
        raise UnsupportedOperatorError(msg)

    def walk_int_constant(self, formula, args, **kwargs):
        return formula
