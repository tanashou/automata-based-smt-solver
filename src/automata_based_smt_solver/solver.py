import logging
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
    DNFGenerator,
    NegationEliminator,
    OrFlattener,
    SymbolCoeffNormalizer,
)
from automata_based_smt_solver.formula.type import FormulaData
from automata_based_smt_solver.sat_status import SatStatus

logger = logging.getLogger(__name__)


class Solver:
    def __init__(self) -> None:
        self.parser = SmtLibParser()
        self._formulas: list[FNode] = []

    def _rewrite_formula_to_cnf(self, formula: FNode) -> FNode:
        cnf = pysmt.rewritings.cnf(formula)
        negation_eliminated_cnf = NegationEliminator().walk(cnf)
        flattened_cnf = OrFlattener().walk(negation_eliminated_cnf)
        distributed = TimesDistributor().walk(flattened_cnf)
        normalized_coeff = SymbolCoeffNormalizer().walk(distributed)
        return CalculatingBracketExpander().walk(normalized_coeff)

    def _rewrite_formula_all_and(self, formula: FNode) -> FNode:
        negation_eliminated_cnf = NegationEliminator().walk(formula)
        flattened_cnf = OrFlattener().walk(negation_eliminated_cnf)
        distributed = TimesDistributor().walk(flattened_cnf)
        normalized_coeff = SymbolCoeffNormalizer().walk(distributed)
        return CalculatingBracketExpander().walk(normalized_coeff)

    def _rewrite_formula_to_dnf(self, formula: FNode) -> Generator[FNode]:
        # 否定を除去してから dnf に変換。変換後の formula には否定が現れない。
        nnf = pysmt.rewritings.nnf(formula)
        negation_eliminated_nnf = NegationEliminator().walk(nnf)
        flattened_nnf = OrFlattener().walk(negation_eliminated_nnf)
        return DNFGenerator().get_conjunctions(flattened_nnf)

    def _extract_data_from_conjunction(self, conjunction: FNode) -> list[FormulaData]:
        times_distributor = TimesDistributor()
        coeff_normalizer = SymbolCoeffNormalizer()
        bracket_expander = CalculatingBracketExpander()

        data_extractor = DataExtractor()

        distributed = times_distributor.walk(conjunction)
        normalized_coeff = coeff_normalizer.walk(distributed)
        expanded = bracket_expander.walk(normalized_coeff)
        if expanded.is_and():
            return [data_extractor.extract(literal) for literal in expanded.args()]
        current_literal = data_extractor.extract(expanded)
        return [current_literal]

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

    def _setup_builders_for_conjunction(
        self,
        conjunction_data: list[FormulaData],
        all_vars: list[FNode],
        var_index_map: dict[FNode, int],
    ) -> list[AutomataBuilder]:
        builders: list[AutomataBuilder] = []
        for literal_data in conjunction_data:
            used_vars = list(literal_data.coeffs.keys())
            builder = AutomataBuilder(
                literal_data,
                all_vars,
                var_index_map,
                used_vars,
                create_all=False,
            )
            builders.append(builder)
        return builders

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

    def _stepwise_build_conjunction(
        self, literal_builders: list[AutomataBuilder]
    ) -> Generator[None]:
        while not all(
            builder.build_status == BuildStatus.COMPLETED
            for builder in literal_builders
        ):
            for builder in literal_builders:
                if builder.build_status == BuildStatus.COMPLETED:
                    continue
                builder.build_step()
            yield

    def _intersect_all_nfa_(self, union_nfas: list[NFA]) -> NFA | None:
        if not union_nfas:
            return None
        all_nfa = union_nfas[0]
        for union_nfa in union_nfas[1:]:
            all_nfa = all_nfa.intersection(union_nfa)
        return all_nfa

    def solve_with_dnf(self) -> SatStatus:
        if not self._formulas:
            msg = "No formulas to solve."
            raise ValueError(msg)

        formula = And(self._formulas)
        logger.info("Solving formula: %s", formula.serialize(threshold=100))
        dnf_generator = self._rewrite_formula_to_dnf(formula)
        logger.info("Rewritten formula to DNF.")

        for i, conjunction in enumerate(dnf_generator):
            logger.info("Processing DNF conjunction #%d", i + 1)
            logger.info(
                "Processing conjunction %s", conjunction.serialize(threshold=100)
            )
            all_vars_in_conj = conjunction.get_free_variables()
            var_index_map = {var: index for index, var in enumerate(all_vars_in_conj)}
            data = self._extract_data_from_conjunction(conjunction)

            literal_builders = self._setup_builders_for_conjunction(
                data, all_vars_in_conj, var_index_map
            )

            for step, _ in enumerate(
                self._stepwise_build_conjunction(literal_builders)
            ):
                logger.info(
                    "intersecting NFA for conjunction #%d step %d", i + 1, step + 1
                )
                all_nfa = self._intersect_all_nfa_(
                    [builder.nfa for builder in literal_builders]
                )
                logger.info(
                    "Finished intersecting NFA for conjunction #%d step %d",
                    i + 1,
                    step + 1,
                )
                if all_nfa and all_nfa.is_acceptable():
                    logger.info("SAT condition found in current conjunction.")
                    return SatStatus.SAT

                logger.info(
                    "Not enough for checking SAT condition yet. Building next step."
                )

        logger.info(
            "No satisfiable conjunction found after checking all possibilities."
        )
        return SatStatus.UNSAT
