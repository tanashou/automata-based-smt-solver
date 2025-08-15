# ruff: noqa: ANN003, ARG002
import pysmt.operators as op
from pysmt.fnode import FNode
from pysmt.shortcuts import Minus
from pysmt.walkers import DagWalker
from pysmt.walkers.generic import handles

from absmt.formula.type import FormulaData, FormulaType, QuantifierType

from .polynomial_normalizer import PolynomialNormalizer


class LiteralDataExtractor(DagWalker):
    """Extracts FormulaData from a single literal (LE or EQUALS)."""

    def __init__(self) -> None:
        super().__init__()
        self.normalizer = PolynomialNormalizer()

    def extract(self, formula: FNode) -> FormulaData:
        return self.walk(formula)

    def walk_lt(self, formula: FNode, args: list, **kwargs) -> FormulaData:
        left, right = formula.arg(0), formula.arg(1)
        expr_to_normalize = Minus(left, right)
        coeffs, const = self.normalizer.walk(expr_to_normalize)
        final_const = -const - 1  # Convert LT to LE by subtracting 1
        return FormulaData(
            quantifier_type=QuantifierType.NONE,
            quantifier_vars=set(),
            coeffs=coeffs,
            const=final_const,
            formula_type=FormulaType.LE,  # Treat LT as LE for automata purposes
        )

    def walk_le(self, formula: FNode, args: list, **kwargs) -> FormulaData:
        left, right = formula.arg(0), formula.arg(1)
        expr_to_normalize = Minus(left, right)
        coeffs, const = self.normalizer.walk(expr_to_normalize)
        final_const = -const
        return FormulaData(
            quantifier_type=QuantifierType.NONE,
            quantifier_vars=set(),
            coeffs=coeffs,
            const=final_const,
            formula_type=FormulaType.LE,
        )

    def walk_equals(self, formula: FNode, args: list, **kwargs) -> FormulaData:
        left, right = formula.arg(0), formula.arg(1)
        expr_to_normalize = Minus(left, right)
        coeffs, const = self.normalizer.walk(expr_to_normalize)
        final_const = -const
        return FormulaData(
            quantifier_type=QuantifierType.NONE,
            quantifier_vars=set(),
            coeffs=coeffs,
            const=final_const,
            formula_type=FormulaType.EQ,
        )

    @handles(
        op.SYMBOL,
        *op.CONSTANTS,
    )
    def walk_others(self, formula: FNode, args: list, **kwargs) -> None:
        return
