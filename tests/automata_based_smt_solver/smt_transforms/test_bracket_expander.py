import itertools

from pysmt.shortcuts import Int, Plus, Symbol, Times
from pysmt.typing import INT

from automata_based_smt_solver.smt_transforms.calculating_bracket_expander import (
    CalculatingBracketExpander,
)


def is_formula_equal(a, b):
    """Recursively check if two formulas are equivalent, handling commutativity."""
    result = False
    if a is b:
        result = True
    elif a.node_type() != b.node_type():
        result = False
    elif a.is_symbol() or a.is_int_constant():
        result = a == b
    elif a.is_plus() or a.is_times():
        # Compare as multisets, recursively
        args_a = list(a.args())
        args_b = list(b.args())
        if len(args_a) != len(args_b):
            result = False
        else:
            result = any(
                all(is_formula_equal(x, y) for x, y in zip(args_a, perm, strict=True))
                for perm in itertools.permutations(args_b)
            )
    else:
        # For other ops, compare recursively in order
        result = all(
            is_formula_equal(x, y) for x, y in zip(a.args(), b.args(), strict=True)
        )
    return result


class TestBracketExpander:
    def setup_method(self):
        self.eliminator = CalculatingBracketExpander()
        self.x = Symbol("x", INT)
        self.y = Symbol("y", INT)
        self.z = Symbol("z", INT)

    def test_flatten_plus(self):
        # x + (y + z) → x + y + z
        term = Plus(self.x, Plus(self.y, self.z))
        result = self.eliminator.walk(term)
        expected = Plus(self.x, self.y, self.z)
        assert is_formula_equal(result, expected), f"Expected {expected}, got {result}"

    def test_flatten_times(self):
        # 2 * (3 * x) → 6 * x
        term = Times(Int(2), Times(Int(3), self.x))
        result = self.eliminator.walk(term)
        expected = Times(Int(6), self.x)
        assert is_formula_equal(result, expected), f"Expected {expected}, got {result}"

    def test_times_int_int(self):
        # 2 * 3 → 6
        term = Times(Int(2), Int(3))
        result = self.eliminator.walk(term)
        expected = Int(6)
        assert is_formula_equal(result, expected), f"Expected {expected}, got {result}"

    def test_plus_int_int(self):
        # 2 + 3 → 5
        term = Plus(Int(2), Int(3))
        result = self.eliminator.walk(term)
        expected = Int(5)
        assert is_formula_equal(result, expected), f"Expected {expected}, got {result}"

    def test_nested_times(self):
        # 2 * (3 * 5) → 30
        term = Times(Int(2), Times(Int(3), Int(5)))
        result = self.eliminator.walk(term)
        expected = Int(30)
        assert is_formula_equal(result, expected), f"Expected {expected}, got {result}"

    def test_nested_times_with_vars(self):
        # 2 * (3 * (5 * x)) → 30 * x
        term = Times(Int(2), Times(Int(3), Times(Int(5), self.x)))
        result = self.eliminator.walk(term)
        expected = Times(Int(30), self.x)
        assert is_formula_equal(result, expected), f"Expected {expected}, got {result}"
