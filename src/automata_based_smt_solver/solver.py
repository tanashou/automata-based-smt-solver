from collections.abc import Generator

import pysmt.rewritings
from pysmt.fnode import FNode
from pysmt.rewritings import TimesDistributor
from pysmt.shortcuts import And
from pysmt.smtlib.parser import SmtLibParser

from automata_based_smt_solver.automata.nfa import NFA
from automata_based_smt_solver.automata_builder import AutomataBuilder
from automata_based_smt_solver.build_status import BuildStatus
from automata_based_smt_solver.formula import DataExtractor
from automata_based_smt_solver.formula.rewritings import (
    CalculatingBracketExpander,
    NegationEliminator,
    OrFlattener,
    SymbolCoeffNormalizer,
)
from automata_based_smt_solver.formula.type import FormulaData
from automata_based_smt_solver.sat_status import SatStatus


class Solver:
    def __init__(self) -> None:
        self.parser = SmtLibParser()
        self._formulas: list[FNode] = []

    def _rewrite_formula(self, formula: FNode) -> FNode:
        cnf = pysmt.rewritings.cnf(formula)
        negation_eliminated_cnf = NegationEliminator().walk(cnf)
        flattened_cnf = OrFlattener().walk(negation_eliminated_cnf)
        distributed = TimesDistributor().walk(flattened_cnf)
        normalized_coeff = SymbolCoeffNormalizer().walk(distributed)
        return CalculatingBracketExpander().walk(normalized_coeff)

    def _extract_data(self, cnf: FNode) -> list[list[FormulaData]]:
        result = []
        data_extractor = DataExtractor()
        if cnf.is_and():
            for clause in cnf.args():
                if clause.is_or():
                    literals = [
                        data_extractor.extract(literal) for literal in clause.args()
                    ]
                    result.append(literals)
                else:
                    literal = data_extractor.extract(clause)
                    result.append([literal])
        elif cnf.is_or():
            literals = [data_extractor.extract(literal) for literal in cnf.args()]
            result.append(literals)
        else:
            literal = data_extractor.extract(cnf)
            result.append([literal])

        return result

    def add(self, formula: FNode) -> None:
        self._formulas.append(formula)

    def _setup_builders(
        self,
        cnf_data: list[list[FormulaData]],
        variables: list[FNode],
        var_index_map: dict[FNode, int],
    ) -> list[list[AutomataBuilder]]:
        cnf_builders: list[list[AutomataBuilder]] = []
        for clause_data in cnf_data:
            clause_builders: list[AutomataBuilder] = []
            for literal_data in clause_data:
                builder = AutomataBuilder(
                    literal_data,
                    variables,
                    var_index_map,
                    create_all=True,  # 現状はこれにする
                )
                clause_builders.append(builder)
            cnf_builders.append(clause_builders)
        return cnf_builders

    def _stepwise_build(
        self, cnf_builders: list[list[AutomataBuilder]]
    ) -> Generator[None]:
        while not all(
            builder.build_status == BuildStatus.COMPLETED
            for clause_builders in cnf_builders
            for builder in clause_builders
        ):
            for clause_builders in cnf_builders:
                for builder in clause_builders:
                    if builder.build_status == BuildStatus.COMPLETED:
                        continue
                    builder.build_step()
                    break
            yield

    def _union_nfas_per_clause(
        self, cnf_builders: list[list[AutomataBuilder]]
    ) -> list[NFA]:
        union_nfas: list[NFA] = []
        for clause_builders in cnf_builders:
            if not clause_builders:
                continue
            union_nfa = clause_builders[0].nfa
            for builder in clause_builders[1:]:
                if builder.build_status != BuildStatus.UNTOUCHED:
                    union_nfa = union_nfa.union(builder.nfa)
            union_nfas.append(union_nfa)
        return union_nfas

    def _intersect_all_nfa_(self, union_nfas: list[NFA]) -> NFA | None:
        if not union_nfas:
            return None
        all_nfa = union_nfas[0]
        for union_nfa in union_nfas[1:]:
            all_nfa = all_nfa.intersection(union_nfa)
        return all_nfa

    def solve(self) -> SatStatus:
        if not self._formulas:
            msg = "No formulas to solve."
            raise ValueError(msg)

        formula = And(self._formulas).simplify()
        cnf = self._rewrite_formula(formula)
        cnf_data = self._extract_data(cnf)
        variables: list[FNode] = sorted(cnf.get_free_variables(), key=lambda v: str(v))
        var_index_map = {name: index for index, name in enumerate(variables)}
        cnf_builders = self._setup_builders(cnf_data, variables, var_index_map)

        for _ in self._stepwise_build(cnf_builders):
            union_nfas = self._union_nfas_per_clause(cnf_builders)
            if not union_nfas:
                msg = "No NFA generated from the CNF clauses."
                raise ValueError(msg)
            all_nfa = self._intersect_all_nfa_(union_nfas)
            if all_nfa and all_nfa.is_acceptable():
                return SatStatus.SAT

        return SatStatus.UNSAT
