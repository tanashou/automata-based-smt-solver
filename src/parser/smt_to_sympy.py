from io import StringIO

import sympy
from pysmt.smtlib.parser import SmtLibParser
from pysmt.walkers import DagWalker
from sympy.logic.boolalg import Boolean


class SMTToSymPy:
    def __init__(self):
        self.sympified_smt = None
        self.sat_status = None  # TODO: sat, unsat, unknown を enum で管理する
        self._converter = PySMTToSymPyConverter()

    def set_smt_script(self, source, is_file=False):
        parser = SmtLibParser()
        if is_file:
            smt_script = parser.get_script_fname(source)
        else:
            smt_script = parser.get_script(StringIO(source))
        self._set_status_info(smt_script)
        smt_script = smt_script.get_strict_formula().simplify()
        self.sympified_smt = self._converter.walk(smt_script)

    def get_sympy_expression_as_dnf(self):
        if not self.sympified_smt:
            msg = "SMT script is not set"
            raise ValueError(msg)
        return sympy.to_dnf(self.sympified_smt)

    def _set_status_info(self, script):
        for cmd in script.commands:
            if cmd.name == "set-info" and cmd.args[0] == ":status":
                self.sat_status = cmd.args[1]
                break

    def rearrange_formula(self, formula):
        lhs, rhs = formula.lhs, formula.rhs

        # Collect all terms with variables on the left
        left_terms = []
        right_terms = []

        for arg in sympy.Add.make_args(lhs - rhs):
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
        raise ValueError("Unsupported formula type")


class PySMTToSymPyConverter(DagWalker):
    def __init__(self):
        super().__init__()

    def walk_symbol(self, formula, args, **kwargs):
        return sympy.Symbol(formula.symbol_name())

    def walk_int_constant(self, formula, args, **kwargs):
        return sympy.Integer(formula.constant_value())

    def walk_real_constant(self, formula, args, **kwargs):
        return sympy.Float(formula.constant_value())

    def walk_and(self, formula, args, **kwargs):
        return sympy.And(*args)

    def walk_or(self, formula, args, **kwargs):
        return sympy.Or(*args)

    def walk_not(self, formula, args, **kwargs):
        return sympy.Not(args[0])

    def walk_equals(self, formula, args, **kwargs):
        return sympy.Eq(*args)

    def walk_le(self, formula, args, **kwargs):
        return sympy.Le(*args)

    def walk_lt(self, formula, args, **kwargs):
        return sympy.Lt(*args)

    def walk_ge(self, formula, args, **kwargs):
        return sympy.Ge(*args)

    def walk_gt(self, formula, args, **kwargs):
        return sympy.Gt(*args)

    def walk_plus(self, formula, args, **kwargs):
        return sympy.Add(*args)

    def walk_minus(self, formula, args, **kwargs):
        if len(args) == 1:
            return -args[0]
        return args[0] - args[1]

    def walk_times(self, formula, args, **kwargs):
        return sympy.Mul(*args)

    def walk_pow(self, formula, args, **kwargs):
        return sympy.Pow(*args)

    def walk_ite(self, formula, args, **kwargs):
        condition, then_branch, else_branch = args

        # If both branches are Boolean, return a Boolean expression
        if isinstance(then_branch, Boolean | bool) and isinstance(
            else_branch, Boolean | bool
        ):
            return sympy.Or(
                sympy.And(condition, then_branch),
                sympy.And(sympy.Not(condition), else_branch),
            )

        # Otherwise, return a Piecewise expression
        return sympy.Piecewise((then_branch, condition), (else_branch, True))
