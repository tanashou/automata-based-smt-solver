from io import StringIO

from pysmt.smtlib.parser import SmtLibParser
from pysmt.smtlib.script import SmtLibScript

from automata_based_smt_solver.parser.sat_status import SatStatus


class FormulaReader:
    def __init__(self, source: str, *, is_file: bool = False) -> None:
        parser = SmtLibParser()
        if is_file:
            smt_script = parser.get_script_fname(source)
        else:
            smt_script = parser.get_script(StringIO(source))
        self.declared_vars = list(map(str, smt_script.get_declared_symbols()))
        self.declared_vars_index_map = {
            var: idx for idx, var in enumerate(self.declared_vars)
        }
        self.sat_status = self._get_sat_status(smt_script)
        self.sympified_smt = self._sympify_smt_script(smt_script)
        self.rearranged_smt = (
            self._rearrange_all_formulas()
        )  # TODO: Solver クラスでやる。色々機能をつけ過ぎ

    def __init__(self):
        self.parser = SmtLibParser()

    def from_smt_lib(self, source: str, *, is_file: bool = False):
        if is_file:
            smt_script = self.parser.get_script_fname(source)
        else:
            smt_script = self.parser.get_script(StringIO(source))
        # SAT 情報と式を返す
        return self._get_sat_status(
            smt_script
        ), smt_script.get_strict_formula().simplify()

    def _get_sat_status(self, script: SmtLibScript) -> SatStatus:
        for cmd in script.commands:
            if cmd.name == "set-info" and cmd.args[0] == ":status":
                return SatStatus(cmd.args[1])
        return SatStatus.UNKNOWN

    # 左辺に変数、右辺に定数を持つ形に変換する
    def _rearrange_formula(self, formula: Relational) -> Relational:
        lhs, rhs = formula.lhs, formula.rhs

        left_terms = []
        right_terms = []

        # lhs, rhs は Relational か numbers なので演算子は使える
        for arg in sympy.Add.make_args(lhs - rhs):  # type: ignore[attr-defined]
            if arg.free_symbols:
                left_terms.append(arg)
            elif isinstance(arg, sympy.Number):
                right_terms.append(-arg)

        new_lhs = sympy.Add(*left_terms)
        new_rhs = sympy.Add(*right_terms)

        # Use the same relation as the original formula
        if isinstance(formula, sympy.Eq):
            return sympy.Eq(new_lhs, new_rhs)
        if isinstance(formula, sympy.Le):
            return sympy.Le(new_lhs, new_rhs)
        if isinstance(formula, sympy.Lt):
            return sympy.Lt(new_lhs, new_rhs)
        if isinstance(formula, sympy.Ge):
            return sympy.Ge(new_lhs, new_rhs)
        if isinstance(formula, sympy.Gt):
            return sympy.Gt(new_lhs, new_rhs)
        msg = "Unsupported formula type"
        raise ValueError(msg)

    def _rearrange_all_formulas(self) -> sympy.Basic:
        if not self.sympified_smt:
            msg = "SMT script is not set"
            raise ValueError(msg)

        def rearrange_recursive(expr: sympy.Basic) -> sympy.Basic:
            if isinstance(expr, sympy.Eq | sympy.Le | sympy.Lt | sympy.Ge | sympy.Gt):
                return self._rearrange_formula(expr)
            if isinstance(expr, sympy.And):
                return sympy.And(*[rearrange_recursive(arg) for arg in expr.args])
            if isinstance(expr, sympy.Or):
                return sympy.Or(*[rearrange_recursive(arg) for arg in expr.args])
            return expr

        return rearrange_recursive(self.sympified_smt)
