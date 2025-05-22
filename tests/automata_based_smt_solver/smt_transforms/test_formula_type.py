from automata_based_smt_solver.formula_rewriter.formula_type import FormulaType


class TestFormulaType:
    def test_enum_values(self):
        """Test that the formula types have the expected values."""
        assert FormulaType.EQ.name == "EQ"
        assert FormulaType.LE.name == "LE"
        assert FormulaType.BOOL.name == "BOOL"

    def test_enum_uniqueness(self):
        """Test that all formula types are unique."""
        formula_types = [FormulaType.EQ, FormulaType.LE, FormulaType.BOOL]
        assert len(formula_types) == len(set(formula_types))
