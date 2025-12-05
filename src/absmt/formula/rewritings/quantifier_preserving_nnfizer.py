# ruff: noqa: ANN201, ANN204, ANN001, ANN003, ARG002

from typing import ClassVar

import pysmt.operators as op
from pysmt.exceptions import (
    PysmtValueError,
)
from pysmt.logics import LIA
from pysmt.oracles import get_logic
from pysmt.rewritings import handles
from pysmt.walkers import DagWalker


class QuantifierPreservingNNFizer(DagWalker):
    """Converts a formula into NNF like, but preserves quantifiers under negation.

    This walker converts expressions like Not(And(A, B)) to Or(Not(A), Not(B)),
    but leaves expressions like Not(ForAll(x, P(x))) unchanged, only applying
    NNF conversion to the subformula P(x) recursively.
    """

    LOGICS: ClassVar[list] = [LIA]

    def __init__(self, environment=None):
        DagWalker.__init__(self, env=environment)
        self.mgr = self.env.formula_manager

    def convert(self, formula):
        logic = get_logic(formula)
        if logic not in self.LOGICS:
            msg = (
                "formula automata builder only "
                "supports LIA or QF_LIA without combination."
                f"(detected logic is: {logic!s})"
            )
            raise PysmtValueError(msg)
        return self.walk(formula)

    def _get_children(self, formula):  # noqa: ANN202, C901, PLR0911
        mgr = self.mgr
        if formula.is_not():
            s = formula.arg(0)
            if s.is_not():
                return [s.arg(0)]
            if s.is_and() or s.is_or():
                return [mgr.Not(x) for x in s.args()]
            if s.is_implies():
                return [s.arg(0), mgr.Not(s.arg(1))]
            if s.is_iff():
                return [s.arg(0), s.arg(1), mgr.Not(s.arg(0)), mgr.Not(s.arg(1))]
            # Do not push negation into quantifiers.
            # Treat the quantifier as an atom-like unit under the Not.
            if s.is_quantifier():
                return [s]  # Return the quantifier itself, not its negated body.
            return [s]

        if formula.is_implies():
            return [mgr.Not(formula.arg(0)), formula.arg(1)]
        if formula.is_iff():
            return [
                formula.arg(0),
                formula.arg(1),
                mgr.Not(formula.arg(0)),
                mgr.Not(formula.arg(1)),
            ]
        if formula.is_and() or formula.is_or() or formula.is_quantifier():
            return formula.args()
        if formula.is_ite():
            if not self.env.stc.get_type(formula).is_bool_type():
                msg = "Expected a boolean type for formula in ITE expression."
                raise ValueError(msg)
            i, t, e = formula.args()
            return [i, mgr.Not(i), t, e]
        if not (
            formula.is_str_op()
            or formula.is_symbol()
            or formula.is_function_application()
            or formula.is_bool_constant()
            or formula.is_theory_relation()
        ):
            raise ValueError(str(formula))
        return []

    def walk_not(self, formula, args, **kwargs):
        s = formula.arg(0)
        if s.is_symbol():
            return self.mgr.Not(s)
        if s.is_not():
            return args[0]
        if s.is_and():
            return self.mgr.Or(args)
        if s.is_or() or s.is_implies():
            return self.mgr.And(args)
        if s.is_iff():
            a, b, na, nb = args
            return self.mgr.Or(self.mgr.And(a, nb), self.mgr.And(b, na))
        return self.mgr.Not(args[0])

    # The rest of the walk_* methods remain the same as the original NNFizer
    def walk_implies(self, formula, args, **kwargs):
        return self.mgr.Or(args)

    def walk_iff(self, formula, args, **kwargs):
        a, b, na, nb = args
        return self.mgr.And(self.mgr.Or(na, b), self.mgr.Or(nb, a))

    def walk_and(self, formula, args, **kwargs):
        return self.mgr.And(args)

    def walk_or(self, formula, args, **kwargs):
        return self.mgr.Or(args)

    def walk_ite(self, formula, args, **kwargs):
        if not self.env.stc.get_type(formula).is_bool_type():
            msg = "Expected a boolean type for formula in ITE expression."
            raise ValueError(msg)
        i, ni, t, e = args
        return self.mgr.And(self.mgr.Or(ni, t), self.mgr.Or(i, e))

    def walk_forall(self, formula, args, **kwargs):
        return self.mgr.ForAll(formula.quantifier_vars(), args[0])

    def walk_exists(self, formula, args, **kwargs):
        return self.mgr.Exists(formula.quantifier_vars(), args[0])

    def walk_symbol(self, formula, **kwargs):
        return formula

    @handles(op.CONSTANTS)
    def walk_constant(self, formula, **kwargs):
        return formula

    @handles(op.RELATIONS)
    def walk_theory_relation(self, formula, **kwargs):
        return formula
