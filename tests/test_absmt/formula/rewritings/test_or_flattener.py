from pysmt.shortcuts import Or, Symbol
from pysmt.typing import BOOL

from absmt.formula.rewritings import OrFlattener


class TestOrFlattener:
    def setup_method(self):
        self.flattener = OrFlattener()
        self.a = Symbol("bv_a", BOOL)
        self.b = Symbol("bv_b", BOOL)
        self.c = Symbol("bv_c", BOOL)
        self.d = Symbol("bv_d", BOOL)

    def test_flatten_nested_or(self):
        # (a OR (b OR c) OR d) should flatten to (a OR b OR c OR d)
        nested = Or(self.a, Or(self.b, self.c), self.d)
        result = self.flattener.walk(nested)
        expected = Or(self.a, self.b, self.c, self.d)
        assert result == expected, f"Expected {expected}, got {result}"

    def test_flatten_deeply_nested_or(self):
        # ((a OR b) OR (c OR d)) should flatten to (a OR b OR c OR d)
        nested = Or(Or(self.a, self.b), Or(self.c, self.d))
        result = self.flattener.walk(nested)
        expected = Or(self.a, self.b, self.c, self.d)
        assert result == expected, f"Expected {expected}, got {result}"

    def test_flatten_single_or(self):
        # (a OR b) should remain (a OR b)
        simple = Or(self.a, self.b)
        result = self.flattener.walk(simple)
        expected = Or(self.a, self.b)
        assert result == expected, f"Expected {expected}, got {result}"
