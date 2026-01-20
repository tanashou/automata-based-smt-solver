from pysmt.shortcuts import Int, Plus, Symbol, Times
from pysmt.typing import BOOL, INT

from absmt.formula.rewritings import (
    SymbolCoeffNormalizer,
)


class TestSymbolCoeffNormalizer:
    def setup_method(self):
        self.normalizer = SymbolCoeffNormalizer()
        self.x = Symbol("x", INT)
        self.y = Symbol("y", INT)
        self.b = Symbol("bv_b", BOOL)

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

    def test_bool_var(self):
        # b (BOOL) -> b (should not be wrapped)
        result = self.normalizer.walk(self.b)
        expected = self.b
        assert result == expected, f"Expected {expected}, got {result}"
