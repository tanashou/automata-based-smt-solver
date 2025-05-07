from pysmt.shortcuts import GT, LE, LT, Equals, Int, Minus, Plus, Symbol, Times
from pysmt.typing import INT

from automata_based_smt_solver.smt_transforms.minus_eliminator import MinusEliminator


class TestMinusEliminator:
    def setup_method(self):
        """Set up common test objects."""
        self.eliminator = MinusEliminator()
        self.x = Symbol("x", INT)
        self.y = Symbol("y", INT)
        self.z = Symbol("z", INT)

    def test_eliminate_simple_minus(self):
        """Test eliminating a simple binary minus operation."""
        # Create test formula: x - y = 0
        formula_minus = Minus(self.x, self.y)
        formula = Equals(formula_minus, Int(0))

        # Apply the minus eliminator
        result = self.eliminator.walk(formula)

        # Expected: x + (-1 * y) = 0  # noqa: ERA001
        expected = Equals(Plus(self.x, Times(Int(-1), self.y)), Int(0))

        assert result == expected, f"Expected {expected}, got {result}"

    def test_eliminate_minus_with_constant(self):
        """Test eliminating minus with a constant operand."""
        # Create test formula: x - 5 > 10
        formula_minus = Minus(self.x, Int(5))
        formula = GT(formula_minus, Int(10))

        # Apply the minus eliminator
        result = self.eliminator.walk(formula)

        # Expected: x + (-5) > 10, which simplifies to x > 15
        expected = GT(Plus(self.x, Int(-5)), Int(10))

        assert result == expected, f"Expected {expected}, got {result}"

    def test_eliminate_minus_with_times(self):
        """Test eliminating minus with a times node as right operand."""
        # Create test formula: x - (2 * y) ≤ 3
        formula_minus = Minus(self.x, Times(Int(2), self.y))
        formula = LE(formula_minus, Int(3))

        # Apply the minus eliminator
        result = self.eliminator.walk(formula)

        # Expected: x + (-2 * y) ≤ 3
        expected = LE(Plus(self.x, Times(Int(-2), self.y)), Int(3))

        assert result == expected, f"Expected {expected}, got {result}"

    def test_eliminate_nested_minus(self):
        """Test eliminating nested minus operations."""
        # Create test formula: x - (y - 3) = 7
        inner_minus = Minus(self.y, Int(3))
        formula_minus = Minus(self.x, inner_minus)
        formula = Equals(formula_minus, Int(7))

        # Apply the minus eliminator
        result = self.eliminator.walk(formula)

        # Expected: x + (-1 * (y + (-1 * 3))) = 7  # noqa: ERA001
        # Which simplifies to: x + (-1 * y) + 3 = 7
        # Or: x - y + 3 = 7  # noqa: ERA001
        expected = Equals(Plus(self.x, Times(Int(-1), Plus(self.y, Int(-3)))), Int(7))

        assert result == expected, f"Expected {expected}, got {result}"

    def test_eliminate_complex_formula(self):
        """Test eliminating minus in a complex formula."""
        # Create test formula: (x - 2*y) - (z - 5) < 0
        left = Minus(self.x, Times(Int(2), self.y))
        right = Minus(self.z, Int(5))
        formula_minus = Minus(left, right)
        formula = LT(formula_minus, Int(0))

        # Apply the minus eliminator
        result = self.eliminator.walk(formula)

        # Expected: x + (-2*y) + (-1 * (z + (-5))) < 0  # noqa: ERA001
        # Which is: x - 2y - z + 5 < 0
        expected = LT(
            Plus(
                Plus(self.x, Times(Int(-2), self.y)),
                Times(Int(-1), Plus(self.z, Int(-5))),
            ),
            Int(0),
        )

        assert result == expected, f"Expected {expected}, got {result}"

    def test_walk_plus_node_unchanged(self):
        """Test that PLUS nodes are not modified."""
        # Create test formula: x + y = 10
        formula_plus = Plus(self.x, self.y)
        formula = Equals(formula_plus, Int(10))

        # Apply the minus eliminator
        result = self.eliminator.walk(formula)

        # Expected: x + y = 10 (unchanged)  # noqa: ERA001
        expected = Equals(Plus(self.x, self.y), Int(10))

        assert result == expected, f"Expected {expected}, got {result}"
