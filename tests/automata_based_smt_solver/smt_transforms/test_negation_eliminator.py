from pysmt.shortcuts import GE, GT, LE, LT, Equals, Not, Or, Symbol
from pysmt.typing import INT

from automata_based_smt_solver.smt_transforms.negation_eliminator import (
    NegationEliminator,
)


# FNode only handle =, <=, <. there is no >= and >.
class TestNegationEliminator:
    def setup_method(self):
        """Set up common test objects."""
        self.eliminator = NegationEliminator()
        self.x = Symbol("x", INT)
        self.y = Symbol("y", INT)
        self.z = Symbol("z", INT)

    def test_eliminate_not_equals(self):
        """Test eliminating negation of equality."""
        # Create test formula: not(x = y)
        formula = Not(Equals(self.x, self.y))

        # Apply the negation eliminator
        result = self.eliminator.walk(formula)

        # Expected: (x < y OR y < x)
        expected = Or(LT(self.x, self.y), LT(self.y, self.x))

        assert result == expected, f"Expected {expected}, got {result}"

    def test_eliminate_not_lt(self):
        """Test eliminating negation of less than."""
        # Create test formula: not(x < y)
        formula = Not(LT(self.x, self.y))

        # Apply the negation eliminator
        result = self.eliminator.walk(formula)

        # Expected: (y <= x)  # noqa: ERA001
        expected = LE(self.y, self.x)

        assert result == expected, f"Expected {expected}, got {result}"

    def test_eliminate_not_le(self):
        """Test eliminating negation of less than or equal."""
        # Create test formula: not(x <= y)
        formula = Not(LE(self.x, self.y))

        # Apply the negation eliminator
        result = self.eliminator.walk(formula)

        # Expected: x > y  # noqa: ERA001
        expected = GT(self.x, self.y)

        assert result == expected, f"Expected {expected}, got {result}"

    def test_eliminate_not_gt(self):
        """Test eliminating negation of greater than."""
        # Create test formula: not(x > y)
        formula = Not(GT(self.x, self.y))

        # Apply the negation eliminator
        result = self.eliminator.walk(formula)

        # Expected: x <= y  # noqa: ERA001
        expected = LE(self.x, self.y)

        assert result == expected, f"Expected {expected}, got {result}"

    def test_eliminate_not_ge(self):
        """Test eliminating negation of greater than or equal."""
        # Create test formula: not(x >= y)
        formula = Not(GE(self.x, self.y))

        # Apply the negation eliminator
        result = self.eliminator.walk(formula)

        # Expected: x < y  # noqa: ERA001
        expected = LT(self.x, self.y)

        assert result == expected, f"Expected {expected}, got {result}"

    def test_double_negation(self):
        """Test elimination of double negation."""
        # Create test formula: not(not(x <= y))
        inner_formula = LE(self.x, self.y)
        formula = Not(Not(inner_formula))

        # Apply the negation eliminator
        result = self.eliminator.walk(formula)

        # Expected: x <= y  # noqa: ERA001
        expected = LE(self.x, self.y)

        assert result == expected, f"Expected {expected}, got {result}"
