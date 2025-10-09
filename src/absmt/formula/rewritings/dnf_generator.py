# ruff: noqa: ANN201, ANN204, ANN001, ANN003, ARG002
import itertools
from collections.abc import Generator

import pysmt.operators as op
from pysmt.fnode import FNode
from pysmt.walkers.dag import DagWalker
from pysmt.walkers.generic import handles


class DNFGenerator(DagWalker):
    """Yields the conjunctions of the DNF of a formula one by one.

    This walker uses DagWalker with memoization invalidated to behave like a
    TreeWalker. This allows the use of 'yield' to create a true Python
    generator that computes each conjunction lazily, only when requested.
    This is highly memory-efficient for formulas that result in a large DNF.
    """

    def __init__(self, env=None):
        # By invalidating memoization, we prevent the walker from caching
        # the one-time-use generators that this class produces.
        DagWalker.__init__(self, env=env, invalidate_memoization=True)
        # Access the formula manager from the environment instance
        self.mgr = self.env.formula_manager

    def get_conjunctions(self, formula) -> Generator[FNode, None, None]:
        """Return a generator that yields the conjunctions of the DNF."""
        # The nnf conversion is a crucial first step for this algorithm
        return self.walk(formula)

    @handles(op.AND)
    def walk_and(self, formula, args, **kwargs) -> Generator[FNode, None, None]:
        # itertools.product is lazy. It creates an iterator that will produce
        # the next combination only when we ask for it.
        product_iterator = itertools.product(*args)

        # We loop through the product iterator. The loop will only advance
        # to the next item when the 'yield' statement is re-entered.
        for conjunctions_tuple in product_iterator:
            literals = []
            for conj in conjunctions_tuple:
                if conj.is_and():
                    literals.extend(conj.args())
                else:
                    literals.append(conj)
            # Yield the new combined conjunction. The function's execution
            # pauses here until the next item is requested from the generator.
            yield self.mgr.And(literals)

    @handles(op.OR)
    def walk_or(self, formula, args, **kwargs):
        # itertools.chain is also lazy. It will exhaust the first generator
        # before starting on the second, all on demand.
        return itertools.chain(*args)

    # This is the corrected handler. It now includes all theory relations
    # (LT, GT, Equals, etc.) as atoms, which fixes the error.
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
    def walk_literal(self, formula, **kwargs) -> Generator[FNode, None, None]:
        if formula.is_false():
            # An empty generator represents a False DNF
            yield from ()
        else:
            yield formula
