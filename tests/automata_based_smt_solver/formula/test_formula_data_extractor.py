import pytest
from pysmt.exceptions import UnsupportedOperatorError
from pysmt.shortcuts import LE, And, Equals, Int, Not, Plus, Symbol, Times
from pysmt.typing import BOOL, INT

from automata_based_smt_solver.formula import DataExtractor
from automata_based_smt_solver.formula.type import FormulaData, FormulaType


# If the coeff of symbol is 1, it should be Times(Int(1), symbol).
# No Minus is allowed. x - y should be represented as x + (-1) * y.
class TestDataExtractor:
    def setup_method(self):
        self.extractor = DataExtractor()
        self.x = Symbol("x", INT)
        self.y = Symbol("y", INT)
        self.z = Symbol("z", INT)
        self.x_coeff_1 = Times(Int(1), self.x)
        self.y_coeff_1 = Times(Int(1), self.y)
        self.z_coeff_1 = Times(Int(1), self.z)

    def test_extract_equality_formula(self):
        """Test extracting data from an equality formula: x + 2*y = 5."""
        const = 5
        x_coeff = 1
        y_coeff = 2
        coeff_count = 2

        two_y = Times(Int(y_coeff), self.y)
        left_side = Plus(self.x_coeff_1, two_y)
        formula = Equals(left_side, Int(const))

        data = self.extractor.extract(formula)

        assert isinstance(data, FormulaData)
        assert data.formula_type == FormulaType.EQ
        assert data.const == const
        assert len(data.coeffs) == coeff_count
        assert data.coeffs[self.x] == x_coeff
        assert data.coeffs[self.y] == y_coeff
        assert not data.has_negation_before_bool_var

    def test_extract_le_formula(self):
        """Test extracting data from a less than or equal formula: x + 3*y <= 10."""
        x_coeff = 1
        y_coeff = 3
        upper_bound = 10
        coeff_count = 2

        y_term = Times(Int(y_coeff), self.y)
        left_side = Plus(self.x_coeff_1, y_term)
        formula = LE(left_side, Int(upper_bound))

        data = self.extractor.extract(formula)

        assert data.formula_type == FormulaType.LE
        assert data.const == upper_bound
        assert len(data.coeffs) == coeff_count
        assert data.coeffs[self.x] == x_coeff
        assert data.coeffs[self.y] == y_coeff
        assert not data.has_negation_before_bool_var

    def test_extract_lt_formula(self):
        """Test extracting data from a less than formula.

        The formula 2*x + y < 7 is expected to be converted to a less-than-or-equal
        formula: 2*x + y <= 6.
        """
        x_coeff = 2
        y_coeff = 1
        upper_bound = 7
        coeff_count = 2
        expected_upper_bound = upper_bound - 1

        from pysmt.shortcuts import LT

        x_term = Times(Int(x_coeff), self.x)
        left_side = Plus(x_term, self.y_coeff_1)
        formula = LT(left_side, Int(upper_bound))

        data = self.extractor.extract(formula)

        assert data.formula_type == FormulaType.LE
        assert data.const == expected_upper_bound
        assert len(data.coeffs) == coeff_count
        assert data.coeffs[self.x] == x_coeff
        assert data.coeffs[self.y] == y_coeff
        assert not data.has_negation_before_bool_var

    def test_extract_bool_formula(self):
        """Test extracting data from a boolean formula: b."""
        expected_coeff = 1
        expected_const = 0

        bv1 = Symbol("BV1", BOOL)

        data = self.extractor.extract(bv1)

        assert data.formula_type == FormulaType.BOOL
        assert data.coeffs[bv1] == expected_coeff
        assert data.const == expected_const
        assert not data.has_negation_before_bool_var

    def test_extract_negated_bool_formula(self):
        """Test extracting data from a negated boolean formula: Not(bv1)."""
        expected_coeff = 1
        expected_const = 0

        bv1 = Symbol("BV1", BOOL)
        formula = Not(bv1)

        data = self.extractor.extract(formula)

        assert data.formula_type == FormulaType.BOOL
        assert data.coeffs[bv1] == expected_coeff
        assert data.const == expected_const
        assert data.has_negation_before_bool_var

    def test_unsupported_operator(self):
        """Test that unsupported operators raise the expected exception (e.g., And)."""
        formula = And(Equals(self.x, Int(1)), Equals(self.y, Int(2)))
        with pytest.raises(UnsupportedOperatorError):
            self.extractor.extract(formula)

    def test_extract_formula_with_multiple_constants_lhs_rhs(self):
        """Test extracting data from a formula with constants on both LHS and RHS.

        x + 2*y + 3 = 5 + 1 is expected to be converted to
        x + 2*y = 5 + 1 - 3 = 3.
        """
        const_rhs = 5
        const_lhs = 3
        x_coeff = 1
        y_coeff = 2
        coeff_count = 2

        two_y = Times(Int(y_coeff), self.y)
        lhs = Plus(self.x_coeff_1, two_y, Int(const_lhs))
        formula = Equals(lhs, Int(const_rhs))

        data = self.extractor.extract(formula)

        # The extractor should move all constants to RHS: x + 2*y = 2
        assert data.formula_type == FormulaType.EQ
        assert data.const == const_rhs - const_lhs
        assert len(data.coeffs) == coeff_count
        assert data.coeffs[self.x] == x_coeff
        assert data.coeffs[self.y] == y_coeff
        assert not data.has_negation_before_bool_var

    def test_extract_formula_with_constants_on_both_sides_le(self):
        """Test extracting data from a LE formula with constants on both sides.

        x + 2*y + 4 <= 10 + 1 is expected to be converted to
        x + 2*y <= 10 + 1 - 4 = 7.
        """
        lhs_const = 4
        rhs_const = 1
        x_coeff = 1
        y_coeff = 2
        upper_bound = 10

        expected_upper_bound = upper_bound + rhs_const - lhs_const

        two_y = Times(Int(y_coeff), self.y)
        lhs = Plus(self.x_coeff_1, two_y, Int(lhs_const))
        rhs = Plus(Int(upper_bound), Int(rhs_const))
        formula = LE(lhs, rhs)

        data = self.extractor.extract(formula)

        assert data.formula_type == FormulaType.LE
        assert data.const == expected_upper_bound
        assert data.coeffs[self.x] == x_coeff
        assert data.coeffs[self.y] == y_coeff
        assert not data.has_negation_before_bool_var

    def test_extract_formula_with_negative_constants(self):
        """Test extracting data from a formula with negative constants.

        x + 2*y - 3 = -5 is expected to be converted to
        x + 2*y = -5 - (-3) = -2.
        """
        lhs_const = -3
        rhs_const = -5
        x_coeff = 1
        y_coeff = 2
        expected_const = rhs_const - lhs_const

        two_y = Times(Int(y_coeff), self.y)
        lhs = Plus(self.x_coeff_1, two_y, Int(lhs_const))
        formula = Equals(lhs, Int(rhs_const))

        data = self.extractor.extract(formula)

        assert data.formula_type == FormulaType.EQ
        assert data.const == expected_const
        assert data.coeffs[self.x] == x_coeff
        assert data.coeffs[self.y] == y_coeff
        assert not data.has_negation_before_bool_var

    def test_extract_formula_with_minus_symbol(self):
        """Test extracting data from a formula with negative coefficients using Minus.

        x - y = -3 should yield coeffs: {x: 1, y: -1}, const: -3
        """
        x_coeff = 1
        y_coeff = -1
        const = -3
        coeff_count = 2

        lhs = Plus(self.x_coeff_1, Times(Int(-1), self.y))
        formula = Equals(lhs, Int(const))

        data = self.extractor.extract(formula)

        assert data.formula_type == FormulaType.EQ
        assert data.const == const
        assert len(data.coeffs) == coeff_count
        assert data.coeffs[self.x] == x_coeff
        assert data.coeffs[self.y] == y_coeff
        assert not data.has_negation_before_bool_var

    def test_extract_var_equals_const(self):
        """Test extracting data from a formula: x = 10."""
        const = 10

        data = self.extractor.extract(Equals(self.x_coeff_1, Int(const)))

        assert data.formula_type == FormulaType.EQ
        assert data.const == const
        assert len(data.coeffs) == 1
        assert data.coeffs[self.x] == 1
        assert not data.has_negation_before_bool_var

    def test_extract_var_times_var_raises(self):
        """Test that extracting data from a formula with var * var raises an error."""
        from pysmt.exceptions import UnsupportedOperatorError

        formula = Equals(Times(self.x, self.y), Int(0))
        with pytest.raises(UnsupportedOperatorError):
            self.extractor.extract(formula)
