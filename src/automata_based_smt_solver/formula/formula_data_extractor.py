# ruff: noqa: ANN201, ANN204, ANN001, ANN003, ARG002, D101, D107, D102
from collections import defaultdict
from dataclasses import dataclass

from pysmt.exceptions import UnsupportedOperatorError
from pysmt.fnode import FNode
from pysmt.typing import BOOL
from pysmt.walkers import DagWalker

from automata_based_smt_solver.formula.formula_type import FormulaType


@dataclass
class FormulaData:
    coeffs: dict[FNode, int]
    vars: set[str]
    const: int
    formula_type: FormulaType
    has_negation_before_bool_var: bool


class FormulaDataExtractor(DagWalker):
    def __init__(self) -> None:
        super().__init__(invalidate_memoization=True)
        self._coeffs: defaultdict[FNode, int] = defaultdict(int)
        self._const: int = 0
        self._formula_type: FormulaType = FormulaType.BOOL
        self._has_negation_before_bool_var: bool = False
        self._side_sign: int = 1

    def extract(self, formula) -> FormulaData:
        self._coeffs = defaultdict(int)
        self._const = 0
        self._formula_type = FormulaType.BOOL
        self._has_negation_before_bool_var = False

        declared_vars = {str(v) for v in formula.get_free_variables()}
        arg_count = 2
        # formulas with bool var have 1 argument
        if len(formula.args()) != arg_count:
            self.walk(formula)
            return FormulaData(
                dict(self._coeffs),
                declared_vars,
                self._const,
                self._formula_type,
                self._has_negation_before_bool_var,
            )

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

        lhs, rhs = formula.args()
        if lhs.is_int_constant():
            self._const -= lhs.constant_value()
        if rhs.is_int_constant():
            self._const += rhs.constant_value()
        self.walk(lhs)
        self._side_sign = -1
        self.walk(rhs)

        final_coeffs = {k: v for k, v in self._coeffs.items() if v != 0}
        return FormulaData(
            final_coeffs,
            declared_vars,
            self._const,
            self._formula_type,
            self._has_negation_before_bool_var,
        )

    # Walker methods

    def walk_not(self, formula, args, **kwargs):
        self._has_negation_before_bool_var = True
        return formula

    def walk_times(self, formula, args, **kwargs):
        expected_arg_count = 2
        if len(args) != expected_arg_count:
            # var with 2 or more degrees exists"
            msg = "TIMES operator must have exactly two arguments."
            raise UnsupportedOperatorError(msg)

        a, b = args
        if a.is_int_constant() and b.is_symbol():
            coeff = a.constant_value() * self._side_sign
            self._coeffs[b] += coeff
        elif a.is_symbol() and b.is_int_constant():
            coeff = b.constant_value() * self._side_sign
            self._coeffs[a] += coeff
        else:
            msg = "TIMES operator must have one int constant and one symbol."
            raise UnsupportedOperatorError(msg)
        return formula

    def walk_plus(self, formula, args, **kwargs):
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

    def walk_symbol(self, formula, args, **kwargs):
        # for bool var, set the coeff to 1. use in AutomataBuilder
        if formula.get_type() == BOOL:
            self._coeffs[formula] = 1
        return formula

    def walk_int_constant(self, formula, args, **kwargs):
        return formula
