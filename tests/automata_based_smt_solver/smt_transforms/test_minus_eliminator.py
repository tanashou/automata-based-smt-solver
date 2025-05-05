from pysmt.shortcuts import GT, LE, Equals, Int, Minus, Plus, Symbol, Times
from pysmt.typing import INT

from automata_based_smt_solver.smt_transforms.formula_data_extractor import (
    FormulaDataExtractor,
)
from automata_based_smt_solver.smt_transforms.minus_eliminator import MinusEliminator


class TestMinusEliminator:
    def setup_method(self):
        """Set up common test objects."""
        self.eliminator = MinusEliminator()
        self.data_extractor = FormulaDataExtractor()
        self.x = Symbol("x", INT)
        self.y = Symbol("y", INT)
        self.z = Symbol("z", INT)

    def verify_formula_data(
        self, formula, expected_vars, expected_coeffs, expected_const=0
    ):
        """Extract and verify formula data for easier comparison."""
        # Extract data from the formula
        formula_data = self.data_extractor.extract(formula)

        # Verify variables
        assert formula_data.vars == expected_vars, (
            f"Expected variables {expected_vars}, got {formula_data.vars}"
        )

        # Verify coefficients
        actual_coeffs = {}
        for node, coeff in formula_data.coeffs.items():
            var_name = str(node)
            actual_coeffs[var_name] = coeff

        for var_node, expected_coeff in expected_coeffs.items():
            var_name = str(var_node)
            assert var_name in actual_coeffs, (
                f"Variable {var_name} not found in coefficients"
            )
            assert actual_coeffs[var_name] == expected_coeff, (
                f"Expected coefficient {expected_coeff} for {var_name}, "
                f"got {actual_coeffs[var_name]}"
            )

        # Verify constant
        assert formula_data.const == expected_const, (
            f"Expected constant {expected_const}, got {formula_data.const}"
        )

    def test_eliminate_simple_minus(self):
        """Test eliminating a simple binary minus operation."""
        # Create test formula: x - y = 0
        formula_minus = Minus(self.x, self.y)
        formula = Equals(formula_minus, Int(0))

        # Apply the minus eliminator
        result = self.eliminator.walk(formula)

        # Verify the result is equivalent to x + (-1 * y) = 0
        assert result.is_equals(), "Result should be an EQUALS node"
        assert result.arg(1).is_int_constant(), "Right side should be an integer const"
        assert result.arg(1).constant_value() == 0, "Right side should be 0"
        self.verify_formula_data(
            result, expected_vars={"x", "y"}, expected_coeffs={self.x: 1, self.y: -1}
        )

    # 左辺に定数があるとバグる
    def test_eliminate_minus_with_constant(self):
        """Test eliminating minus with a constant operand."""
        # Define test constants
        constant_value = 5
        expected_value = 10

        # Create test formula: x - 5 > 10
        formula_minus = Minus(self.x, Int(constant_value))
        formula = GT(formula_minus, Int(expected_value))

        # Apply the minus eliminator
        result = self.eliminator.walk(formula)

        # Verify the right side of the equation still has expected value
        assert result.arg(1).is_int_constant(), (
            "Right side should be an integer constant"
        )
        assert result.arg(1).constant_value() == expected_value, (
            f"Right side should be {expected_value}"
        )

        # Verify the left side is now x + (-5)
        left_side = result.arg(0)
        assert left_side.is_plus(), "Left side should be a PLUS node"

        # Verify the result via FormulaDataExtractor
        self.verify_formula_data(
            result,
            expected_vars={"x"},
            expected_coeffs={self.x: 1},
            expected_const=-10,  # GT gets converted to LE with negation
        )

    def test_eliminate_minus_with_times(self):
        """Test eliminating minus with a times node as right operand."""
        # Define test constants
        multiplier = 2
        expected_bound = 3

        # Create test formula: x - (2 * y) ≤ 3
        formula_minus = Minus(self.x, Times(Int(multiplier), self.y))
        formula = LE(formula_minus, Int(expected_bound))

        # Apply the minus eliminator
        result = self.eliminator.walk(formula)

        # Verify the formula structure
        assert result.is_le(), "Result should be a LE node"
        assert result.arg(1).is_int_constant(), (
            "Right side should be an integer constant"
        )
        assert result.arg(1).constant_value() == expected_bound, (
            f"Right side should be {expected_bound}"
        )

        # Verify the result is equivalent to x + (-2 * y) ≤ 3
        self.verify_formula_data(
            result,
            expected_vars={"x", "y"},
            expected_coeffs={self.x: 1, self.y: -multiplier},
            expected_const=expected_bound,
        )

    # fix: '(x + (-1 * (y + (-1 * 3))))'となる。
    def test_eliminate_nested_minus(self):
        """Test eliminating nested minus operations."""
        # Define test constants
        constant_value = 3

        # Create test formula: x - (y - 3) = 7
        inner_minus = Minus(self.y, Int(constant_value))
        formula_minus = Minus(self.x, inner_minus)
        formula = Equals(formula_minus, Int(7))
        formula = formula.simplify()

        # Apply the minus eliminator
        result = self.eliminator.walk(formula)

        # Verify the result has no MINUS nodes
        assert not self._contains_minus(result), (
            "Result should not contain any MINUS nodes"
        )

        # The result should be equivalent to x - y + 3 = 7
        self.verify_formula_data(
            result,
            expected_vars={"x", "y"},
            expected_coeffs={self.x: 1, self.y: -1},
            expected_const=4,  # The constant on the right side
        )

    # fix 定数が左辺に現れるとうまく処理できない
    def test_eliminate_complex_formula(self):
        """Test eliminating minus in a complex formula."""
        # Create test formula: (x - 2*y) - (z - 5) < 0
        left = Minus(self.x, Times(Int(2), self.y))
        right = Minus(self.z, Int(5))
        formula_minus = Minus(left, right)
        formula = LE(formula_minus, Int(-1))  # LT gets converted to LE with -1

        # Apply the minus eliminator
        result = self.eliminator.walk(formula)

        # Verify no MINUS nodes remain
        assert not self._contains_minus(result), (
            "Result should not contain any MINUS nodes"
        )

        # Verify the formula is properly transformed
        self.verify_formula_data(
            result,
            expected_vars={"x", "y", "z"},
            expected_coeffs={self.x: 1, self.y: -2, self.z: -1},
            expected_const=-1,  # This is the constant from LE
        )

    def test_walk_plus_node_unchanged(self):
        """Test that PLUS nodes are not modified."""
        # Define constants
        constant_value = 10

        # Create test formula: x + y = 10
        formula_plus = Plus(self.x, self.y)
        formula = Equals(formula_plus, Int(constant_value))

        # Apply the minus eliminator
        result = self.eliminator.walk(formula)

        # Verify the result is unchanged structurally
        assert result.is_equals(), "Result should be an EQUALS node"
        assert result.arg(0).is_plus(), "Left side should still be a PLUS node"
        assert result.arg(1).is_int_constant(), (
            "Right side should be an integer constant"
        )
        assert result.arg(1).constant_value() == constant_value, (
            f"Right side should be {constant_value}"
        )

        # Verify formula semantics are preserved
        self.verify_formula_data(
            result,
            expected_vars={"x", "y"},
            expected_coeffs={self.x: 1, self.y: 1},
            expected_const=10,
        )

    def _contains_minus(self, formula) -> bool:
        """Check if a formula contains any MINUS nodes."""
        if formula.is_minus():
            return True
        return any(self._contains_minus(arg) for arg in formula.args())

    def _has_coeff_and_var(self, times_node, coeff, var) -> bool:
        """Check if a TIMES node has the specified coefficient and variable.

        Helper method for verifying coefficient-variable pairs in TIMES nodes.
        """
        if not times_node.is_times():
            return False

        if times_node.arg(0).is_int_constant() and times_node.arg(1) == var:
            return times_node.arg(0).constant_value() == coeff
        if times_node.arg(1).is_int_constant() and times_node.arg(0) == var:
            return times_node.arg(1).constant_value() == coeff

        return False
