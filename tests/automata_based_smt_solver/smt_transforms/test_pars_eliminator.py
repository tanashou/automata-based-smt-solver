from pysmt.shortcuts import Int, Minus, Plus, Symbol, Times
from pysmt.typing import INT

from automata_based_smt_solver.smt_transforms.pars_eliminator import ParsEliminator


class TestParsEliminator:
    def setup_method(self):
        self.eliminator = ParsEliminator()
        self.x = Symbol("x", INT)
        self.y = Symbol("y", INT)
        self.z = Symbol("z", INT)

    def test_distribute_times_over_plus(self):
        # 2 * (y + z) → 2*y + 2*z
        term = Times(Int(2), Plus(self.y, self.z))
        result = self.eliminator.walk(term)
        expected = Plus(Times(Int(2), self.y), Times(Int(2), self.z))
        assert result == expected, f"Expected {expected}, got {result}"

    def test_distribute_times_left_plus(self):
        # (x + y) * 3 → x*3 + y*3
        term = Times(Plus(self.x, self.y), Int(3))
        result = self.eliminator.walk(term)
        expected = Plus(Times(self.x, Int(3)), Times(self.y, Int(3)))
        assert result == expected, f"Expected {expected}, got {result}"

    def test_distribute_minus_right_plus(self):
        # x - (y + z) → x - y - z
        term = Minus(self.x, Plus(self.y, self.z))
        result = self.eliminator.walk(term)
        expected = Minus(Minus(self.x, self.y), self.z)
        assert result == expected, f"Expected {expected}, got {result}"

    def test_distribute_minus_left_plus(self):
        # (x + y) - z → x + y - z
        term = Minus(Plus(self.x, self.y), self.z)
        result = self.eliminator.walk(term)
        expected = Minus(Plus(self.x, self.y), self.z)
        assert result == expected, f"Expected {expected}, got {result}"

    def test_flatten_plus(self):
        # x + (y + z) → x + y + z
        term = Plus(self.x, Plus(self.y, self.z))
        result = self.eliminator.walk(term)
        expected = Plus(self.x, self.y, self.z)
        assert result == expected, f"Expected {expected}, got {result}"

    def test_flatten_times(self):
        # 2 * (3 * x) → 6 * x
        term = Times(Int(2), Times(Int(3), self.x))
        result = self.eliminator.walk(term)
        expected = Times(Int(6), self.x)
        assert result == expected, f"Expected {expected}, got {result}"

    def test_times_int_int(self):
        # 2 * 3 → 6
        term = Times(Int(2), Int(3))
        result = self.eliminator.walk(term)
        expected = Int(6)
        assert result == expected, f"Expected {expected}, got {result}"

    def test_plus_int_int(self):
        # 2 + 3 → 5
        term = Plus(Int(2), Int(3))
        result = self.eliminator.walk(term)
        expected = Int(5)
        assert result == expected, f"Expected {expected}, got {result}"

    def test_minus_int_int(self):
        # 5 - 3 → 2
        term = Minus(Int(5), Int(3))
        result = self.eliminator.walk(term)
        expected = Int(2)
        assert result == expected, f"Expected {expected}, got {result}"

    def test_distribute_negative_times_over_plus(self):
        # -2 * (y + 3) → -2*y - 6
        term = Times(Int(-2), Plus(self.y, Int(3)))
        result = self.eliminator.walk(term)
        expected = Plus(Times(Int(-2), self.y), Int(-6))
        assert result == expected, f"Expected {expected}, got {result}"
