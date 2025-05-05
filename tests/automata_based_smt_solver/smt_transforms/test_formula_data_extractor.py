import pytest
from pysmt.exceptions import UnsupportedOperatorError
from pysmt.shortcuts import (
    GE,
    GT,
    LE,
    LT,
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

    def test_extract_le_formula(self):
        """Test extracting data from a less than or equal formula."""
        # Define constants
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
        assert data.coeffs[x] == 1
        assert data.coeffs[y] == y_coeff
        assert data.vars == {"x", "y"}
        assert not data.has_negation_before_bool_var

    def test_extract_lt_formula(self):
        """Test extracting data from a less than formula."""
        upper_bound = 5
        expected_const = 4  # LT x < 5 becomes LE x <= 4

        x = Symbol("x", INT)
        formula = LT(x, Int(upper_bound))

        extractor = FormulaDataExtractor()
        data = extractor.extract(formula)

        assert data.formula_type == FormulaType.LE
        assert data.const == expected_const
        assert data.coeffs[x] == 1
        assert data.vars == {"x"}
        assert not data.has_negation_before_bool_var

    def test_extract_gt_formula(self):
        """Test extracting data from a greater than formula."""
        lower_bound = 5
        expected_coeff = -1  # Should be negated for GT

        x = Symbol("x", INT)
        formula = GT(x, Int(lower_bound))

        extractor = FormulaDataExtractor()
        data = extractor.extract(formula)

        # GT should be converted to LE with negated coefficients
        assert data.formula_type == FormulaType.LE
        assert data.coeffs[x] == expected_coeff
        assert data.vars == {"x"}
        assert not data.has_negation_before_bool_var

    def test_extract_ge_formula(self):
        """Test extracting data from a greater than or equal formula."""
        lower_bound = 1000  # Similar to (>= x1 1000) in the SMT2 file
        expected_coeff = -1  # Should be negated for GE

        x = Symbol("x", INT)
        formula = GE(x, Int(lower_bound))

        extractor = FormulaDataExtractor()
        data = extractor.extract(formula)

        # GE should be converted to LE with negated coefficients
        assert data.formula_type == FormulaType.LE
        assert data.coeffs[x] == expected_coeff
        assert data.vars == {"x"}
        assert not data.has_negation_before_bool_var

    def test_extract_bool_formula(self):
        """Test extracting data from a boolean formula."""
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
