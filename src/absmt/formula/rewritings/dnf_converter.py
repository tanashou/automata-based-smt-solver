# ruff: noqa: ANN204, ANN001, ANN003, ARG002
import itertools
from typing import ClassVar

import pysmt.operators as op
from pysmt.exceptions import (
    PysmtValueError,
)
from pysmt.fnode import FNode
from pysmt.logics import QF_LIA
from pysmt.oracles import get_logic
from pysmt.walkers.dag import DagWalker
from pysmt.walkers.generic import handles


class DNFConverter(DagWalker):
    """Converts a formula to DNF. The input formula is assumed to be in NNF."""

    LOGICS: ClassVar[list] = [QF_LIA]

    def __init__(self, env=None):
        # DagWalker keeps a cache (memoization) so that shared subformulas
        # are processed only once. We do NOT invalidate memoization here
        # because we are returning static FNodes, not one-time generators.
        DagWalker.__init__(self, env=env)
        self.mgr = self.env.formula_manager

    def convert(self, formula) -> list[FNode]:
        logic = get_logic(formula)
        if not any(logic <= allowed_logic for allowed_logic in self.LOGICS):
            msg = (
                "formula automata builder only supports QF_LIA."
                f"(detected logic is: {logic!s})"
            )
            raise PysmtValueError(msg)

        dnf = self.walk(formula)
        return self._get_conjunctions(dnf)

    def _get_conjunctions(self, formula) -> list[FNode]:
        if formula.is_or():
            return formula.args()
        return [formula]

    @handles(op.AND)
    def walk_and(self, formula, args, **kwargs) -> FNode:
        # args contains the DNF FNodes of the children.
        # We need to compute the Cartesian product of their conjunctions.
        # (A | B) & (C | D) => (A&C) | (A&D) | (B&C) | (B&D)

        # Prepare lists of conjunctions for each child
        children_conjunctions = [self._get_conjunctions(arg) for arg in args]

        # itertools.product computes the distribution logic
        new_conjunctions = []
        for conjunction_tuple in itertools.product(*children_conjunctions):
            literals = []
            for conj in conjunction_tuple:
                # Flatten nested ANDs: (x & y) & z => x & y & z
                if conj.is_and():
                    literals.extend(conj.args())
                elif conj.is_true():
                    continue
                else:
                    literals.append(conj)
            new_conjunctions.append(self.mgr.And(literals))

        return self.mgr.Or(new_conjunctions)

    @handles(op.OR)
    def walk_or(self, formula, args, **kwargs) -> FNode:
        # Flatten nested ORs: (A | B) | C => A | B | C
        disjuncts = []
        for arg in args:
            if arg.is_or():
                disjuncts.extend(arg.args())
            else:
                disjuncts.append(arg)
        return self.mgr.Or(disjuncts)

    @handles(
        op.SYMBOL,
        op.NOT,
        op.BOOL_CONSTANT,
        op.INT_CONSTANT,
        op.LT,
        op.LE,
        op.EQUALS,
        op.TIMES,
        op.PLUS,
        op.MINUS,
    )
    def walk_literal(self, formula, **kwargs) -> FNode:
        # Leaves (literals) are returned as is.
        return formula
