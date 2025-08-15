# ruff: noqa: ANN003, ARG002
import collections

from pysmt.fnode import FNode
from pysmt.walkers import DagWalker


class PolynomialNormalizer(DagWalker):
    """Walker to normalize LIA arithmetic expressions.

    Example: Times(2, x) + 5 - y  ->  ({x: 2, y: -1}, 5)
    """

    def __init__(self) -> None:
        super().__init__()

    def walk_plus(self, formula: FNode, args: list, **kwargs) -> tuple:
        # Aggregate results from child nodes
        res_coeffs = collections.defaultdict(int)
        res_const = 0
        for coeffs, const in args:
            for var, coeff_val in coeffs.items():
                res_coeffs[var] += coeff_val
            res_const += const
        return dict(res_coeffs), res_const

    def walk_minus(self, formula: FNode, args: list, **kwargs) -> tuple:
        # (coeffs1, const1) - (coeffs2, const2)  # noqa: ERA001
        (coeffs1, const1), (coeffs2, const2) = args
        res_coeffs = collections.defaultdict(int, coeffs1)
        for var, coeff_val in coeffs2.items():
            res_coeffs[var] -= coeff_val
        res_const = const1 - const2
        return dict(res_coeffs), res_const

    def walk_times(self, formula: FNode, args: list, **kwargs) -> tuple:
        # For linear arithmetic, one side must be a constant
        (coeffs1, const1), (coeffs2, const2) = args

        if not coeffs1 and coeffs2:  # const1 * (coeffs2, const2)
            factor = const1
            target_coeffs, target_const = coeffs2, const2
        elif not coeffs2 and coeffs1:  # (coeffs1, const1) * const2
            factor = const2
            target_coeffs, target_const = coeffs1, const1
        elif not coeffs1 and not coeffs2:  # const1 * const2
            return {}, const1 * const2
        else:
            msg = f"Non-linear arithmetic is not supported: {formula}"
            raise NotImplementedError(msg)

        res_coeffs = {var: val * factor for var, val in target_coeffs.items()}
        res_const = target_const * factor
        return res_coeffs, res_const

    def walk_int_constant(self, formula: FNode, args: list, **kwargs) -> tuple:
        # Return integer constant as ({}, value)
        return {}, formula.constant_value()

    def walk_real_constant(self, formula: FNode, args: list, **kwargs) -> tuple:
        # Intended for LIA, but allows extension to LRA
        val = formula.constant_value()
        if val.denominator != 1:
            msg = f"LIA formula contains non-integer constant: {val}"
            raise TypeError(msg)
        return {}, val.numerator

    def walk_symbol(self, formula: FNode, args: list, **kwargs) -> tuple:
        # Only consider INT or REAL type symbols
        if formula.symbol_type().is_int_type() or formula.symbol_type().is_real_type():
            return {formula.symbol_name(): 1}, 0
        # Symbols of type BOOL should not appear in arithmetic expressions
        return {}, 0
