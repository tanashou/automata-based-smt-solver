from pysmt.shortcuts import LT, Equals, Int, Minus, Not, Symbol
from pysmt.typing import INT

from automata_based_smt_solver.smt_transforms.formula_rewriter import (
    FormulaRewriter,
)


class TestFormulaRewriter:
    def setup_method(self):
        self.formula_rewriter = FormulaRewriter()
        self.x = Symbol("x", INT)
        self.y = Symbol("y", INT)

    def test_cnfize_equality(self):
        formula = Equals(self.x, self.y)
        result = self.formula_rewriter.cnfize_and_rewrite(formula)
        assert result.is_equals()
        assert {str(v) for v in result.get_free_variables()} == {"x", "y"}

    def test_cnfize_inequality(self):
        formula = LT(self.x, self.y)
        result = self.formula_rewriter.cnfize_and_rewrite(formula)
        assert result.is_lt() or result.is_le() or result.is_or()
        assert {str(v) for v in result.get_free_variables()} == {"x", "y"}

    def test_minus_elimination(self):
        formula = Equals(Minus(self.x, self.y), Int(0))
        result = self.formula_rewriter.cnfize_and_rewrite(formula)
        assert result.is_equals()
        left = result.arg(0)
        assert left.is_plus()
        assert any(
            arg.is_times()
            and arg.arg(0).is_int_constant()
            and arg.arg(0).constant_value() == -1
            for arg in left.args()
        )

    def test_negation_elimination(self):
        formula = Not(Equals(self.x, self.y))
        result = self.formula_rewriter.cnfize_and_rewrite(formula)
        assert result.is_or()
        args = result.args()
        assert any(arg.is_lt() for arg in args)
