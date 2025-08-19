# ruff: noqa: ANN001, ANN003, ARG002

import contextlib
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
        all_vars += [str(var) for var in QuantVarCollector().collect(formula)]
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

        quantifier_vars = formula.quantifier_vars()
        spot_nfa = args[0]
        res = SpotNFA.projection(spot_nfa, quantifier_vars)
        logger.info(res.to_hoa())
        # res is a SpotNFA instance; best-effort debug printing
        with contextlib.suppress(Exception):
            formula_str = str(formula)
            logger.info(
                "Showing automaton for 'exists' (quantified vars=%s) formula=%s",
                quantifier_vars,
                formula_str,
            )
            res.show()
        return res

    def walk_and(self, formula: FNode, args: list[SpotNFA], **kwargs) -> SpotNFA:
        res = SpotNFA.intersect_all(*args)
        logger.info(res.to_hoa())
        # intersect_all returns a SpotNFA; best-effort debug printing
        with contextlib.suppress(Exception):
            formula_str = str(formula)
            logger.info(
                "Showing automaton for 'and' with %d operands; formula=%s",
                len(args),
                formula_str,
            )
            res.show()
        return res

    def walk_or(self, formula: FNode, args: list[SpotNFA], **kwargs) -> SpotNFA:
        res = SpotNFA.union_all(*args)
        logger.info(res.to_hoa())
        # best-effort debug printing
        with contextlib.suppress(Exception):
            formula_str = str(formula)
            logger.info(
                "Showing automaton for 'or' with %d operands; formula=%s",
                len(args),
                formula_str,
            )
            res.show()
        return res

    def walk_not(self, formula: FNode, args: list[SpotNFA], **kwargs) -> SpotNFA:
        if len(args) != 1:
            msg = "The body of a NOT expression must be represented as a single nfa."
            raise ValueError(msg)
        res = SpotNFA.complement(args[0])
        logger.info(res.to_hoa())
        with contextlib.suppress(Exception):
            formula_str = str(formula)
            logger.info("Showing automaton for 'not'; formula=%s", formula_str)
            res.show()
        return res

    @handles(op.LT, op.LE, op.EQUALS)
    def walk_literal(self, formula: FNode, args, **kwargs) -> SpotNFA:
        literal_data = self._literal_data_extractor.extract(formula)
        all_vars = kwargs["all_vars"]
        all_var_index_map = kwargs["all_var_index_map"]

        builder = AutomataBuilder(literal_data, all_vars, all_var_index_map)
        nfa = builder.build()
        res = SpotNFA(nfa, self._bdict)
        logger.info(res.to_hoa())
        with contextlib.suppress(Exception):
            # include a short description from literal_data if possible
            # Use repr for a stable, non-raising description
            lit_desc = repr(literal_data)
            formula_str = str(formula)
            logger.info(
                "Showing automaton for 'literal': %s; formula=%s",
                lit_desc,
                formula_str,
            )
            res.show()
        return res

    @handles(
        op.SYMBOL,
        *op.CONSTANTS,
        *op.IRA_OPERATORS,
    )
    def walk_others(self, formula: FNode, args, **kwargs) -> None:
        return


class QuantVarCollector(DagWalker):
    """A simple walker to collect quantifier variables from a formula."""

    def __init__(self) -> None:
        super().__init__()
        self.quantifier_vars: set[str] = set()

    def collect(self, formula: FNode) -> set[str]:
        """Collect quantifier variables from the given formula."""
        self.walk(formula)
        return self.quantifier_vars

    def walk_exists(self, formula: FNode, args, **kwargs) -> None:
        self.quantifier_vars.update(formula.quantifier_vars())

    @handles(
        op.SYMBOL,
        *op.BOOL_CONNECTIVES,
        *op.CONSTANTS,
        *op.RELATIONS,
        *op.IRA_OPERATORS,
    )
    def walk_others(self, formula: FNode, args, **kwargs) -> None:
        """Handle other formula types without collecting quantifier variables."""
        return
