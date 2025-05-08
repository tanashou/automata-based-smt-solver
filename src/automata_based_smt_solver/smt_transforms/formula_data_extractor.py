# ruff: noqa: ANN201, ANN204, ANN001, ANN003, ARG002, D101, D107, D102
from dataclasses import dataclass

from pysmt.exceptions import UnsupportedOperatorError
from pysmt.fnode import FNode
from pysmt.walkers import DagWalker

from automata_based_smt_solver.smt_transforms.formula_type import FormulaType


@dataclass
class FormulaData:
    coeffs: dict[FNode, int]
    vars: set[str]
    const: int
    formula_type: FormulaType
    has_negation_before_bool_var: bool


class FormulaDataExtractor(DagWalker):
    def __init__(self) -> None:
        super().__init__()
        self._coeffs: dict[FNode, int] = {}
        self._const: int = 0
        self._formula_type: FormulaType = FormulaType.BOOL  # eq, le, bool のどれか
        self._has_negation_before_bool_var: bool = False

    def _collect_coeffs_and_const(self, node) -> tuple[dict, int]:
        coeffs = {}
        const = 0

        def helper(n, sign=1) -> None:
            if n.is_symbol():
                coeffs[n] = coeffs.get(n, 0) + sign
            elif n.is_int_constant():
                nonlocal const
                const += sign * n.constant_value()
            elif n.is_times():
                args = n.args()
                if args[0].is_int_constant() and args[1].is_symbol():
                    coeffs[args[1]] = (
                        coeffs.get(args[1], 0) + sign * args[0].constant_value()
                    )
                elif args[1].is_int_constant() and args[0].is_symbol():
                    coeffs[args[0]] = (
                        coeffs.get(args[0], 0) + sign * args[1].constant_value()
                    )
                else:
                    msg = "TIMES operator must have one constant and one symbol."
                    raise UnsupportedOperatorError(msg)
            elif n.is_plus():
                for arg in n.args():
                    helper(arg, sign)
            elif n.is_minus():
                helper(n.arg(0), sign)
                helper(n.arg(1), -sign)
            else:
                msg = f"Unsupported node in linear formula: {n}"
                raise UnsupportedOperatorError(msg)

        helper(node)
        return coeffs, const

    def extract(self, formula) -> FormulaData:
        self.walk(formula)
        declared_vars = {str(v) for v in formula.get_free_variables()}
        arg_count = 2
        if len(formula.args()) != arg_count:
            return FormulaData(
                self._coeffs,
                declared_vars,
                self._const,
                self._formula_type,
                self._has_negation_before_bool_var,
            )
        lhs, rhs = formula.args()
        lhs_coeffs, lhs_const = self._collect_coeffs_and_const(lhs)
        rhs_coeffs, rhs_const = self._collect_coeffs_and_const(rhs)
        final_coeffs = {}
        for k, v in lhs_coeffs.items():
            final_coeffs[k] = final_coeffs.get(k, 0) + v
        for k, v in rhs_coeffs.items():
            final_coeffs[k] = final_coeffs.get(k, 0) - v
        final_const = rhs_const - lhs_const
        # Remove zero coefficients
        final_coeffs = {k: v for k, v in final_coeffs.items() if v != 0}
        return FormulaData(
            final_coeffs,
            declared_vars,
            final_const,
            self._formula_type,
            self._has_negation_before_bool_var,
        )

    # Walker methods

    def walk_not(self, formula, args, **kwargs):
        self._has_negation_before_bool_var = True
        return formula

    def walk_times(self, formula, args, **kwargs):
        a, b = formula.args()

        if a.is_constant() and b.is_symbol():
            coeff = a.constant_value()
            self._coeffs[b] = coeff
        elif b.is_constant() and a.is_symbol():
            coeff = b.constant_value()
            self._coeffs[a] = coeff
        else:
            msg = "TIMES operator must have one constant and one symbol."
            raise UnsupportedOperatorError(msg)
        return formula

    def walk_plus(self, formula, **kwargs):
        pass

    def walk_minus(self, formula, args, **kwargs):
        pass

    def walk_symbol(self, formula, args, **kwargs):
        # For symbols not part of a TIMES node, assign default coefficient.
        if formula not in self._coeffs:
            self._coeffs[formula] = 1
        return formula

    def walk_equals(self, formula, args, **kwargs):
        self._formula_type = FormulaType.EQ
        return formula

    def walk_le(self, formula, args, **kwargs):
        self._formula_type = FormulaType.LE
        return formula

    def walk_lt(self, formula, args, **kwargs):
        # Transpose the formula to a <= relation.
        self._const = -1
        self._formula_type = FormulaType.LE
        return formula

    def walk_int_constant(self, formula, args, **kwargs):
        pass

    def walk_and(self, formula, args, **kwargs):
        msg = (
            "Logical 'and' is not allowed. Please eliminate it before using this "
            "extractor."
        )
        raise UnsupportedOperatorError(msg)

    def walk_or(self, formula, args, **kwargs):
        msg = (
            "Logical 'or' is not allowed. Please eliminate it before using this "
            "extractor."
        )
        raise UnsupportedOperatorError(msg)
