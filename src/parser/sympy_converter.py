import sympy
from pysmt.walkers import DagWalker


class SymPyConverter(DagWalker):
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
        return sympy.Piecewise((args[1], args[0]), (args[2], True))
