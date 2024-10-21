from io import StringIO

import sympy
from pysmt.smtlib.parser import SmtLibParser
from pysmt.smtlib.script import SmtLibScript
from sympy.core.relational import Relational
from sympy.logic.boolalg import BooleanFunction

from parser.pysmt_to_sympy_converter import PySMTToSymPyConverter
from parser.sat_status import SatStatus


class SMTToSymPy:
    def __init__(self) -> None:
        self.sympified_smt = None
        self.rearranged_smt = None
        self.sat_status = None
        self._converter = PySMTToSymPyConverter()

    def set_smt_script(self, source: str, *, is_file: bool = False) -> None:
        parser = SmtLibParser()
        if is_file:
            smt_script = parser.get_script_fname(source)
        else:
            smt_script = parser.get_script(StringIO(source))
        self._set_status_info(smt_script)
        smt_script = smt_script.get_strict_formula().simplify()
        self.sympified_smt = self._converter.walk(smt_script)

    def get_sympy_expression_as_dnf(self) -> BooleanFunction:
        if not self.sympified_smt:
            msg = "SMT script is not set"
            raise ValueError(msg)
        return sympy.to_dnf(self.sympified_smt)

    def _set_status_info(self, script: SmtLibScript) -> None:
        for cmd in script.commands:
            if cmd.name == "set-info" and cmd.args[0] == ":status":
                self.sat_status = SatStatus(cmd.args[1])
                break

    # 左辺に変数、右辺に定数を持つ形に変換する
    def rearrange_formula(self, formula: Relational) -> Relational:
        lhs, rhs = formula.lhs, formula.rhs

        # Collect all terms with variables on the left
        left_terms = []
        right_terms = []

        for arg in sympy.Add.make_args(sympy.simplify(lhs) - sympy.simplify(rhs)):
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

    def rearrange_all_formulas(self) -> sympy.Basic:
        if not self.sympified_smt:
            msg = "SMT script is not set"
            raise ValueError(msg)

        def rearrange_recursive(expr: sympy.Basic) -> sympy.Basic:
            if isinstance(expr, sympy.Eq | sympy.Le | sympy.Lt | sympy.Ge | sympy.Gt):
                return self.rearrange_formula(expr)
            if isinstance(expr, sympy.And):
                return sympy.And(*[rearrange_recursive(arg) for arg in expr.args])
            if isinstance(expr, sympy.Or):
                return sympy.Or(*[rearrange_recursive(arg) for arg in expr.args])
            return expr

        self.rearranged_smt = rearrange_recursive(self.sympified_smt)
        return self.rearranged_smt

    def get_rearranged_sympy_expression(self) -> sympy.Basic:
        if self.rearranged_smt is None:
            self.rearrange_all_formulas()
        if self.rearranged_smt is None:
            msg = "SMT script is not set"
            raise ValueError(msg)
        return self.rearranged_smt

    def get_rearranged_sympy_expression_as_dnf(self) -> BooleanFunction:
        if self.rearranged_smt is None:
            self.rearrange_all_formulas()
        return sympy.to_dnf(self.rearranged_smt)
