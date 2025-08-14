# ruff: noqa: ANN001, ANN003, ARG002
import pysmt.operators as op
import spot
from pysmt.fnode import FNode
from pysmt.walkers import DagWalker
from pysmt.walkers.generic import handles

from absmt.automata.spot_nfa import SpotNFA
from absmt.automata_builder import AutomataBuilder
from absmt.formula import LiteralDataExtractor


class FormulaAutomataBuilder(DagWalker):
    def __init__(self) -> None:
        super().__init__()
        self._literal_data_extractor = LiteralDataExtractor()
        self._bdict = spot.make_bdd_dict()

    def build(self, formula: FNode) -> SpotNFA:
        all_vars = [str(var) for var in formula.get_free_variables()]
        all_vars += [str(var) for var in formula.quantifier_vars()]
        all_var_index_map = {var: index for index, var in enumerate(all_vars)}
        walk_context = {
            "all_vars": all_vars,
            "all_var_index_map": all_var_index_map,
        }
        return self.walk(formula, **walk_context)

    def walk_exists(self, formula: FNode, args: list[SpotNFA], **kwargs) -> SpotNFA:
        if len(args) != 1:
            msg = (
                "The body of an exists expression must be represented as a single nfa. "
            )
            raise ValueError(msg)

        quantifier_vars = formula.quantifier_vars()
        spot_nfa = args[0]
        return SpotNFA.projection(spot_nfa, quantifier_vars)

    def walk_and(self, formula: FNode, args: list[SpotNFA], **kwargs) -> SpotNFA:
        return SpotNFA.intersect_all(*args)

    def walk_or(self, formula: FNode, args: list[SpotNFA], **kwargs) -> SpotNFA:
        return SpotNFA.union_all(*args)

    def walk_not(self, formula: FNode, args: list[SpotNFA], **kwargs) -> SpotNFA:
        if len(args) != 1:
            msg = "The body of a NOT expression must be represented as a single nfa."
            raise ValueError(msg)
        return SpotNFA.complement(args[0])

    @handles(op.LE, op.EQUALS)
    def walk_literal(self, formula: FNode, args, **kwargs) -> SpotNFA:
        literal_data = self._literal_data_extractor.extract(formula)
        all_vars = kwargs["all_vars"]
        all_var_index_map = kwargs["all_var_index_map"]

        builder = AutomataBuilder(literal_data, all_vars, all_var_index_map)
        nfa = builder.build()
        return SpotNFA(nfa, self._bdict)
