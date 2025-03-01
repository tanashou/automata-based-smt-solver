# ruff: noqa: ANN201, ANN204, ANN001, ANN003, ARG002, D101, D107, D102
from dataclasses import dataclass

from pysmt.exceptions import UnsupportedOperatorError
from pysmt.fnode import FNode
from pysmt.walkers import DagWalker

from smt_solver.formula.formula_type import FormulaType


@dataclass
class FormulaData:
    coeffs: dict[FNode, int]
    vars: set[str]
    const: int
    formula_type: FormulaType
    has_not: bool


class FormulaDataExtractor(DagWalker):
    def __init__(self) -> None:
        super().__init__()
        self._coeffs: dict[FNode, int] = {}
        self._const: int = 0
        self._formula_type: FormulaType = FormulaType.BOOL  # eq, le, bool のどれか
        self._has_not: bool = False

    def extract(self, formula) -> FormulaData:
        # 数式なら =, <= として各種パラメータを取得する。
        # boolean var なら係数は0 として取得する。
        self.walk(formula)

        declared_vars = {str(v) for v in formula.get_free_variables()}

        # 左辺と右辺があるので2。not は除去されているため考えなくていい。
        if len(formula.args()) != 2:  # noqa: PLR2004
            # boolean var の場合
            return FormulaData(
                self._coeffs,
                declared_vars,
                self._const,
                self._formula_type,
                self._has_not,
            )
        lhs, rhs = formula.args()
        # FNode の Simplify により、定数が現れるなら左辺、右辺のどちらかは定数のみ
        if lhs.is_int_constant():
            # 定数が左辺にあるので、右辺に移動させる
            self._const += -lhs.constant_value()
            # 変数が右辺あるので、左辺に移動させる
            for k, v in self._coeffs.items():
                self._coeffs[k] = -v
        elif rhs.is_int_constant():
            self._const += rhs.constant_value()
        else:
            lhs_vars = lhs.get_free_variables()
            rhs_vars = rhs.get_free_variables()
            for k, v in self._coeffs.items():
                if k in lhs_vars:
                    self._coeffs[k] = v
                elif k in rhs_vars:
                    self._coeffs[k] = -v

        return FormulaData(
            self._coeffs, declared_vars, self._const, self._formula_type, self._has_not
        )

    # Walker methods

    def walk_not(self, formula, args, **kwargs):
        self._has_not = True
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
            if formula.get_type().is_bool_type():
                self._coeffs[formula] = 0
            else:
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
        msg = "Logical 'and' is not supported in linear constraints."
        raise UnsupportedOperatorError(msg)

    def walk_or(self, formula, args, **kwargs):
        msg = "Logical 'or' is not supported in linear constraints."
        raise UnsupportedOperatorError(msg)
