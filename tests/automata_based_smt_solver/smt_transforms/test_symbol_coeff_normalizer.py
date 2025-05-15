from pysmt.shortcuts import Int, Plus, Symbol, Times
from pysmt.typing import INT

from automata_based_smt_solver.smt_transforms.symbol_coeff_normalizer import (
    SymbolCoeffNormalizer,
)


class TestSymbolCoeffNormalizer:
    def setup_method(self):
        self.normalizer = SymbolCoeffNormalizer()
        self.x = Symbol("x", INT)
        self.y = Symbol("y", INT)

    def test_symbol_is_wrapped(self):
        # x -> 1 * x
        result = self.normalizer.walk(self.x)
        expected = Times(Int(1), self.x)
        assert result == expected, f"Expected {expected}, got {result}"

    def test_already_wrapped(self):
        # 1 * x -> 1 * (1 * x)
        expr = Times(Int(1), self.x)
        result = self.normalizer.walk(expr)
        expected = Times(Int(1), expr)
        assert result == expected, f"Expected {expected}, got {result}"

    def test_multiple_symbols(self):
        # x + y -> 1 * x + 1 * y
        result = self.normalizer.walk(Plus(self.x, self.y))
        expected = Plus(Times(Int(1), self.x), Times(Int(1), self.y))
        assert result == expected, f"Expected {expected}, got {result}"

    def test_nested_parens(self):
        # 3 * (x + y) -> 3 * (1 * x + 1 * y)
        expr = Times(Int(3), Plus(self.x, self.y))
        result = self.normalizer.walk(expr)
        expected = Times(Int(3), Plus(Times(Int(1), self.x), Times(Int(1), self.y)))
        assert result == expected, f"Expected {expected}, got {result}"
