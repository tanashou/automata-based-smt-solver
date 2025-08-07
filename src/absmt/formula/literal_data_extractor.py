# ruff: noqa: ANN003, ARG002
from pysmt.fnode import FNode
from pysmt.shortcuts import Minus
from pysmt.walkers import DagWalker

from absmt.formula.type import FormulaData, FormulaType, QuantifierType

from .polynomial_normalizer import PolynomialNormalizer


class LiteralDataExtractor(DagWalker):
    """Extracts FormulaData from a single literal (LE or EQUALS)."""

    def __init__(self) -> None:
        super().__init__()
        self.normalizer = PolynomialNormalizer()

    def extract(self, formula: FNode) -> FormulaData:
        return self.walk(formula)

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
