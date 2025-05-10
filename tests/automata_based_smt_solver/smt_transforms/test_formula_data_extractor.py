import pytest
from pysmt.exceptions import UnsupportedOperatorError
from pysmt.shortcuts import LE, And, Equals, Int, Minus, Not, Plus, Symbol, Times
from pysmt.typing import BOOL, INT

from automata_based_smt_solver.smt_transforms.formula_data_extractor import (
    FormulaData,
    FormulaDataExtractor,
)
from automata_based_smt_solver.smt_transforms.formula_type import FormulaType


class TestFormulaDataExtractor:
    """Test only formulas with a single integer constant."""

    def test_extract_equality_formula(self):
        """Test extracting data from an equality formula: x + 2*y = 5."""
        const = 5
        x_coeff = 1
        y_coeff = 2
        coeff_count = 2

        x = Symbol("x", INT)
        y = Symbol("y", INT)
        two_y = Times(Int(y_coeff), y)
        left_side = Plus(x, two_y)
        formula = Equals(left_side, Int(const))

        extractor = FormulaDataExtractor()
        data = extractor.extract(formula)

        assert isinstance(data, FormulaData)
        assert data.formula_type == FormulaType.EQ
        assert data.const == const
        assert len(data.coeffs) == coeff_count
        assert data.coeffs[x] == x_coeff
        assert data.coeffs[y] == y_coeff
        assert data.vars == {"x", "y"}
        assert not data.has_negation_before_bool_var

    def test_extract_le_formula(self):
        """Test extracting data from a less than or equal formula: x + 3*y <= 10."""
        x_coeff = 1
        y_coeff = 3
        upper_bound = 10
        coeff_count = 2

        x = Symbol("x", INT)
        y = Symbol("y", INT)
        formula = LE(Plus(x, Times(Int(y_coeff), y)), Int(upper_bound))

        extractor = FormulaDataExtractor()
        data = extractor.extract(formula)

        assert data.formula_type == FormulaType.LE
        assert data.const == upper_bound
        assert len(data.coeffs) == coeff_count
        assert data.coeffs[x] == x_coeff
        assert data.coeffs[y] == y_coeff
        assert data.vars == {"x", "y"}
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

        x = Symbol("x", INT)
        y = Symbol("y", INT)
        from pysmt.shortcuts import LT

        formula = LT(Plus(Times(Int(x_coeff), x), y), Int(upper_bound))

        extractor = FormulaDataExtractor()
        data = extractor.extract(formula)

        assert data.formula_type == FormulaType.LE
        assert data.const == expected_upper_bound
        assert len(data.coeffs) == coeff_count
        assert data.coeffs[x] == x_coeff
        assert data.coeffs[y] == y_coeff
        assert data.vars == {"x", "y"}
        assert not data.has_negation_before_bool_var

    def test_extract_bool_formula(self):
        """Test extracting data from a boolean formula: b."""
        expected_coeff = 1
        expected_const = 0

        b = Symbol("b", BOOL)

        extractor = FormulaDataExtractor()
        data = extractor.extract(b)

        assert data.formula_type == FormulaType.BOOL
        assert data.coeffs[b] == expected_coeff
        assert data.const == expected_const
        assert data.vars == {"b"}
        assert not data.has_negation_before_bool_var

    def test_extract_negated_bool_formula(self):
        """Test extracting data from a negated boolean formula: Not(b)."""
        expected_coeff = 1
        expected_const = 0

        b = Symbol("b", BOOL)
        formula = Not(b)

        extractor = FormulaDataExtractor()
        data = extractor.extract(formula)

        assert data.formula_type == FormulaType.BOOL
        assert data.coeffs[b] == expected_coeff
        assert data.const == expected_const
        assert data.vars == {"b"}
        assert data.has_negation_before_bool_var

    def test_unsupported_operator(self):
        """Test that unsupported operators raise the expected exception (e.g., And)."""
        x = Symbol("x", INT)
        y = Symbol("y", INT)
        formula = And(Equals(x, Int(1)), Equals(y, Int(2)))
        extractor = FormulaDataExtractor()
        with pytest.raises(UnsupportedOperatorError):
            extractor.extract(formula)

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

        x = Symbol("x", INT)
        y = Symbol("y", INT)
        lhs = Plus(x, Times(Int(y_coeff), y), Int(const_lhs))
        formula = Equals(lhs, Int(const_rhs))

        extractor = FormulaDataExtractor()
        data = extractor.extract(formula)

        # The extractor should move all constants to RHS: x + 2*y = 2
        assert data.formula_type == FormulaType.EQ
        assert data.const == const_rhs - const_lhs
        assert len(data.coeffs) == coeff_count
        assert data.coeffs[x] == x_coeff
        assert data.coeffs[y] == y_coeff
        assert data.vars == {"x", "y"}
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

        x = Symbol("x", INT)
        y = Symbol("y", INT)
        lhs = Plus(x, Times(Int(y_coeff), y), Int(lhs_const))
        rhs = Plus(Int(upper_bound), Int(rhs_const))
        formula = LE(lhs, rhs)

        extractor = FormulaDataExtractor()
        data = extractor.extract(formula)

        assert data.formula_type == FormulaType.LE
        assert data.const == expected_upper_bound
        assert data.coeffs[x] == x_coeff
        assert data.coeffs[y] == y_coeff
        assert data.vars == {"x", "y"}
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

        x = Symbol("x", INT)
        y = Symbol("y", INT)
        lhs = Plus(x, Times(Int(y_coeff), y), Int(lhs_const))
        formula = Equals(lhs, Int(rhs_const))

        extractor = FormulaDataExtractor()
        data = extractor.extract(formula)

        assert data.formula_type == FormulaType.EQ
        assert data.const == expected_const
        assert data.coeffs[x] == x_coeff
        assert data.coeffs[y] == y_coeff
        assert data.vars == {"x", "y"}
        assert not data.has_negation_before_bool_var

    def test_extract_formula_with_minus_symbol(self):
        """Test extracting data from a formula with negative coefficients using Minus.

        x - y = -3 should yield coeffs: {x: 1, y: -1}, const: -3
        """
        x_coeff = 1
        y_coeff = -1
        const = -3
        coeff_count = 2

        x = Symbol("x", INT)
        y = Symbol("y", INT)

        lhs = Minus(x, y)
        formula = Equals(lhs, Int(const))

        extractor = FormulaDataExtractor()
        data = extractor.extract(formula)

        assert data.formula_type == FormulaType.EQ
        assert data.const == const
        assert len(data.coeffs) == coeff_count
        assert data.coeffs[x] == x_coeff
        assert data.coeffs[y] == y_coeff
        assert data.vars == {"x", "y"}
        assert not data.has_negation_before_bool_var
