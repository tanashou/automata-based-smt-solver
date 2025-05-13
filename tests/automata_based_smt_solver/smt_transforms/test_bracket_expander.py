import itertools

from pysmt.rewritings import TimesDistributor
from pysmt.shortcuts import Int, Minus, Plus, Symbol, Times
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
        self.distributor = TimesDistributor()
        self.x = Symbol("x", INT)
        self.y = Symbol("y", INT)
        self.z = Symbol("z", INT)

    def test_distribute_times_over_plus(self):
        # 2 * (y + z) → 2*y + 2*z
        term = Times(Int(2), Plus(self.y, self.z))
        term = self.distributor.walk(term)
        result = self.eliminator.walk(term)
        expected = Plus(Times(Int(2), self.y), Times(Int(2), self.z))
        assert is_formula_equal(result, expected), f"Expected {expected}, got {result}"

    def test_distribute_times_left_plus(self):
        # (x + y) * 3 → x*3 + y*3
        term = Times(Plus(self.x, self.y), Int(3))
        term = self.distributor.walk(term)
        result = self.eliminator.walk(term)
        expected = Plus(Times(self.x, Int(3)), Times(self.y, Int(3)))
        assert is_formula_equal(result, expected), f"Expected {expected}, got {result}"

    def test_distribute_minus_right_plus(self):
        # x - (y + z) → x - y - z
        term = Minus(self.x, Plus(self.y, self.z))
        term = self.distributor.walk(term)
        result = self.eliminator.walk(term)
        expected = Plus(self.x, Times(self.y, Int(-1)), Times(self.z, Int(-1)))
        assert is_formula_equal(result, expected), f"Expected {expected}, got {result}"

    def test_distribute_minus_left_plus(self):
        # (x + y) - z → x + y - z
        term = Minus(Plus(self.x, self.y), self.z)
        term = self.distributor.walk(term)
        result = self.eliminator.walk(term)
        expected = Plus(self.x, self.y, Times(self.z, Int(-1)))
        assert is_formula_equal(result, expected), f"Expected {expected}, got {result}"

    def test_flatten_plus(self):
        # x + (y + z) → x + y + z
        term = Plus(self.x, Plus(self.y, self.z))
        term = self.distributor.walk(term)
        result = self.eliminator.walk(term)
        expected = Plus(self.x, self.y, self.z)
        assert is_formula_equal(result, expected), f"Expected {expected}, got {result}"

    def test_flatten_times(self):
        # 2 * (3 * x) → 6 * x
        term = Times(Int(2), Times(Int(3), self.x))
        term = self.distributor.walk(term)
        result = self.eliminator.walk(term)
        expected = Times(Int(6), self.x)
        assert is_formula_equal(result, expected), f"Expected {expected}, got {result}"

    def test_times_int_int(self):
        # 2 * 3 → 6
        term = Times(Int(2), Int(3))
        term = self.distributor.walk(term)
        result = self.eliminator.walk(term)
        expected = Int(6)
        assert is_formula_equal(result, expected), f"Expected {expected}, got {result}"

    def test_plus_int_int(self):
        # 2 + 3 → 5
        term = Plus(Int(2), Int(3))
        term = self.distributor.walk(term)
        result = self.eliminator.walk(term)
        expected = Int(5)
        assert is_formula_equal(result, expected), f"Expected {expected}, got {result}"

    def test_minus_int_int(self):
        # 5 - 3 → 2
        term = Minus(Int(5), Int(3))
        term = self.distributor.walk(term)
        result = self.eliminator.walk(term)
        expected = Int(2)
        assert is_formula_equal(result, expected), f"Expected {expected}, got {result}"

    def test_distribute_negative_times_over_plus(self):
        # -2 * (y + 3) → -2*y - 6
        term = Times(Int(-2), Plus(self.y, Int(3)))
        term = self.distributor.walk(term)
        result = self.eliminator.walk(term)
        expected = Plus(Times(Int(-2), self.y), Int(-6))
        assert is_formula_equal(result, expected), f"Expected {expected}, got {result}"

    def test_times_with_multiple_plus(self):
        # 2 * (3 + x + y) → 6 + 2*x + 2*y
        term = Times(Int(2), Plus(Int(3), self.x, self.y))
        term = self.distributor.walk(term)
        result = self.eliminator.walk(term)
        expected = Plus(Int(6), Times(Int(2), self.x), Times(Int(2), self.y))
        assert is_formula_equal(result, expected), f"Expected {expected}, got {result}"

    def test_nested_times(self):
        # 2 * (3 * 5) → 30
        term = Times(Int(2), Times(Int(3), Int(5)))
        term = self.distributor.walk(term)
        result = self.eliminator.walk(term)
        expected = Int(30)
        assert is_formula_equal(result, expected), f"Expected {expected}, got {result}"

    def test_nested_times_with_vars(self):
        # 2 * (3 * (5 * x)) → 30 * x
        term = Times(Int(2), Times(Int(3), Times(Int(5), self.x)))
        term = self.distributor.walk(term)
        result = self.eliminator.walk(term)
        expected = Times(Int(30), self.x)
        assert is_formula_equal(result, expected), f"Expected {expected}, got {result}"

    def test_nested_pars_with_times(self):
        # 2 * (3 * (1 + x) + y) → 6 + 6*x + 2*y
        term = Times(Int(2), Plus(Times(Int(3), Plus(Int(1), self.x)), self.y))
        term = self.distributor.walk(term)
        result = self.eliminator.walk(term)
        expected = Plus(Int(6), Times(Int(6), self.x), Times(Int(2), self.y))
        assert is_formula_equal(result, expected), f"Expected {expected}, got {result}"
