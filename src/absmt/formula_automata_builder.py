# ruff: noqa: ANN001, ANN003, ARG002

import logging

import pysmt.operators as op
import spot
from pysmt.fnode import FNode
from pysmt.walkers import DagWalker
from pysmt.walkers.generic import handles

from absmt.automata.spot_nfa import SpotNFA
from absmt.automata_builder import AutomataBuilder
from absmt.formula import LiteralDataExtractor

logger = logging.getLogger(__name__)


class FormulaAutomataBuilder(DagWalker):
    def __init__(self) -> None:
        super().__init__()
        self._literal_data_extractor = LiteralDataExtractor()
        self._bdict = spot.make_bdd_dict()

    def build(self, formula: FNode) -> SpotNFA:
        all_vars = [str(var) for var in formula.get_free_variables()]
        all_var_index_map = {var: index for index, var in enumerate(all_vars)}
        walk_context = {
            "all_vars": all_vars,
            "all_var_index_map": all_var_index_map,
        }
        return self.walk(formula, **walk_context)

    def _get_key(self, formula: FNode, *args: list, **kwargs) -> FNode:
        return formula

    def walk_exists(self, formula: FNode, args: list[SpotNFA], **kwargs) -> SpotNFA:
        if len(args) != 1:
            msg = (
                "The body of an exists expression must be represented as a single nfa. "
            )
            raise ValueError(msg)

        all_vars = kwargs["all_vars"]
        quantifier_vars = formula.quantifier_vars()
        spot_nfa = args[0]

        formula_str = formula.serialize(threshold=20)
        logger.debug(
            "Prepared automaton for 'exists'; formula=%s",
            formula_str,
        )

        res = SpotNFA.projection(spot_nfa, all_vars, quantifier_vars)

        logger.debug(
            "Showing automaton for 'exists'; formula=%s",
            formula_str,
        )
        return res

    def walk_and(self, formula: FNode, args: list[SpotNFA], **kwargs) -> SpotNFA:
        formula_str = formula.serialize(threshold=20)
        logger.debug(
            "Building automaton for 'and' with %d operands; formula=%s",
            len(args),
            formula_str,
        )

        res = SpotNFA.intersect_all(*args)

        logger.debug("Complete building for 'and'.")

        return res

    def walk_or(self, formula: FNode, args: list[SpotNFA], **kwargs) -> SpotNFA:
        formula_str = formula.serialize(threshold=20)
        logger.debug(
            "Building automaton for 'or' with %d operands; formula=%s",
            len(args),
            formula_str,
        )

        res = SpotNFA.union_all(*args)

        logger.debug("Complete building for 'or'.")
        return res

    def walk_not(self, formula: FNode, args: list[SpotNFA], **kwargs) -> SpotNFA:
        if len(args) != 1:
            msg = "The body of a NOT expression must be represented as a single nfa."
            raise ValueError(msg)
        res = SpotNFA.complement(args[0])
        formula_str = formula.serialize(threshold=20)
        logger.debug("Prepared automaton for 'not'; formula=%s", formula_str)
        return res

    @handles(op.LT, op.LE, op.EQUALS)
    def walk_literal(self, formula: FNode, args, **kwargs) -> SpotNFA:
        literal_data = self._literal_data_extractor.extract(formula)
        all_vars = kwargs["all_vars"]
        all_var_index_map = kwargs["all_var_index_map"]

        builder = AutomataBuilder(literal_data, all_vars, all_var_index_map)
        nfa = builder.build()
        res = SpotNFA(nfa, self._bdict)
        formula_str = formula.serialize(threshold=20)
        logger.debug(
            "Prepared automaton for 'literal'; formula=%s",
            formula_str,
        )

        return res

    @handles(
        op.SYMBOL,
        *op.CONSTANTS,
        *op.IRA_OPERATORS,
    )
    def walk_others(self, formula: FNode, args, **kwargs) -> None:
        return
