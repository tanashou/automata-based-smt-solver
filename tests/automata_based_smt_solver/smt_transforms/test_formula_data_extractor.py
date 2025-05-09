import pytest
from pysmt.exceptions import UnsupportedOperatorError
from pysmt.shortcuts import (
    LE,
    And,
    Equals,
    Int,
    Not,
    Plus,
    Symbol,
    Times,
)
from pysmt.typing import BOOL, INT

from automata_based_smt_solver.smt_transforms.formula_data_extractor import (
    FormulaData,
    FormulaDataExtractor,
)
from automata_based_smt_solver.smt_transforms.formula_type import FormulaType


class TestFormulaDataExtractor:
    """Only need to test eq, le, and bool."""

    def test_extract_equality_formula(self):
        """Test extracting data from an equality formula."""
        # Create a formula: x + 2*y = 5
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

        # Verify extracted data
        assert isinstance(data, FormulaData)
        assert data.formula_type == FormulaType.EQ
        assert data.const == const
        assert len(data.coeffs) == coeff_count
        assert data.coeffs[x] == x_coeff
        assert data.coeffs[y] == y_coeff
        assert data.vars == {"x", "y"}
        assert not data.has_negation_before_bool_var

    def test_extract_equality_formula_with_two_constants(self):
        """Test extracting data from equality formula with constants on both sides."""
        # Create formula x + (-5) = 10
        x = Symbol("x", INT)
        left_side = Plus(x, Int(-5))
        right_side = Int(10)
        formula = Equals(left_side, right_side)

        # Expected results after normalization: x = 15
        expected_const = 15
        expected_coeff = 1

        extractor = FormulaDataExtractor()
        data = extractor.extract(formula)

        assert data.formula_type == FormulaType.EQ
        assert data.const == expected_const
        assert data.coeffs[x] == expected_coeff
        assert data.vars == {"x"}
        assert not data.has_negation_before_bool_var

    def test_extract_equality_formula_with_multiple_constants(self):
        """Test extracting data from equality formula with multiple constants."""
        # Create formula x + 2 + (-5) + 8 = 10 + 3
        x = Symbol("x", INT)
        left_side = Plus(x, Int(2), Int(-5), Int(8))
        right_side = Plus(Int(10), Int(3))
        formula = Equals(left_side, right_side)

        # Expected results after normalization: x = 13 - 2 + 5 - 8 = 8
        expected_const = 8
        expected_coeff = 1

        extractor = FormulaDataExtractor()
        data = extractor.extract(formula)

        assert data.formula_type == FormulaType.EQ
        assert data.const == expected_const
        assert data.coeffs[x] == expected_coeff
        assert data.vars == {"x"}
        assert not data.has_negation_before_bool_var

    def test_extract_le_formula(self):
        """Test extracting data from a less than or equal formula."""
        # Define constants
        # Create a formula: x + 3*y <= 10
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

    def test_extract_le_formula_with_multiple_constants_and_vars(self):
        """Test extracting <= formula with multiple consts and vars on both sides."""
        # Create formula: x + 2 + 3*y + 7 = 10 + 4 + 2*z + y
        x = Symbol("x", INT)
        y = Symbol("y", INT)
        z = Symbol("z", INT)
        left_side = Plus(x, Int(2), Times(Int(3), y), Int(7))
        right_side = Plus(Int(10), Int(4), Times(Int(2), z), y)
        formula = LE(left_side, right_side)
        # After normalization, we get: x + 2*y - 2*z <= 5
        # So: x:1, y:2, z:-2, const: 5
        extractor = FormulaDataExtractor()
        data = extractor.extract(formula)

        expected_const = 5
        expected_coeff_x = 1
        expected_coeff_y = 2
        expected_coeff_z = -2

        assert data.formula_type == FormulaType.LE
        assert data.coeffs[x] == expected_coeff_x
        assert data.coeffs[y] == expected_coeff_y
        assert data.coeffs[z] == expected_coeff_z
        assert data.const == expected_const
        assert data.vars == {"x", "y", "z"}
        assert not data.has_negation_before_bool_var

    def test_extract_bool_formula(self):
        """Test extracting data from a boolean formula."""
        # Create a boolean formula: b
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
        """Test extracting data from a negated boolean formula."""
        # Create a negated boolean formula: Not(b)
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
        """Test that unsupported operators raise the expected exception."""
        # Create a formula with an unsupported operator (AND)
        x = Symbol("x", INT)
        y = Symbol("y", INT)

        # Create formula with AND operator which isn't allowed in this extractor
        formula = And(Equals(x, Int(1)), Equals(y, Int(2)))

        extractor = FormulaDataExtractor()
        with pytest.raises(UnsupportedOperatorError):
            extractor.extract(formula)

    def test_with_smt2_file(self, int_incompleteness1_formula):
        """Test the FormulaDataExtractor with formulas from an SMT2 file."""
        # Setup extractor
        extractor = FormulaDataExtractor()
        extracted_data = extractor.extract(int_incompleteness1_formula)

        # Verify data structure is correct
        assert isinstance(extracted_data, FormulaData), (
            "Should return FormulaData instance"
        )

        # Test formula_type - int_incompleteness1 contains an equality: 3x1 + 3x2 = 1
        assert extracted_data.formula_type == FormulaType.EQ, (
            "Should be an equality constraint"
        )

        # Test const - right side of the equation is 1
        assert extracted_data.const == 1, "Constant term should be 1"

        # Test vars - should have x1 and x2
        assert extracted_data.vars == {"x1", "x2"}, "Should contain variables x1 and x2"

        # Test coeffs - should have coefficients for x1 and x2, both equal to 3
        coeffs_count = 2
        assert len(extracted_data.coeffs) == coeffs_count

        # Find the FNode keys for x1 and x2
        x1_node = next(k for k in extracted_data.coeffs if str(k) == "x1")
        x2_node = next(k for k in extracted_data.coeffs if str(k) == "x2")

        # Verify coefficients are correct
        x1_coeff = 3
        x2_coeff = 3
        assert extracted_data.coeffs[x1_node] == x1_coeff
        assert extracted_data.coeffs[x2_node] == x2_coeff
        # Test has_negation_before_bool_var - no negation in this formula
        assert not extracted_data.has_negation_before_bool_var, (
            "Should not have boolean negation"
        )

    def test_extract_nested_parentheses_with_multiplication(self):
        """Test extracting data from a formula with nested parentheses."""
        # Create formula: 2 * (x + 3*y + (z + 4)) = 20
        x = Symbol("x", INT)
        y = Symbol("y", INT)
        z = Symbol("z", INT)
        inner = Plus(z, Int(4))
        left_side = Times(Int(2), Plus(x, Times(Int(3), y), inner))
        right_side = Int(20)
        formula = Equals(left_side, right_side)
        formula.simplify()

        extractor = FormulaDataExtractor()
        data = extractor.extract(formula)

        # Expected: 2*x + 6*y + 2*z = 12  # noqa: ERA001
        expected_const = 12
        expected_coeff_x = 2
        expected_coeff_y = 6
        expected_coeff_z = 2
        assert data.formula_type == FormulaType.EQ
        assert data.coeffs[x] == expected_coeff_x
        assert data.coeffs[y] == expected_coeff_y
        assert data.coeffs[z] == expected_coeff_z
        assert data.const == expected_const
        assert data.vars == {"x", "y", "z"}
        assert not data.has_negation_before_bool_var
