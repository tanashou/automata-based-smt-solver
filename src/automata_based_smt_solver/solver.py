import pysmt.rewritings
from pysmt.fnode import FNode
from pysmt.rewritings import TimesDistributor
from pysmt.smtlib.parser import SmtLibParser

from automata_based_smt_solver.smt_transforms.calculating_bracket_expander import (
    CalculatingBracketExpander,
)
from automata_based_smt_solver.smt_transforms.formula_data_extractor import (
    FormulaData,
    FormulaDataExtractor,
)
from automata_based_smt_solver.smt_transforms.negation_eliminator import (
    NegationEliminator,
)
from automata_based_smt_solver.smt_transforms.or_flattener import OrFlattener
from automata_based_smt_solver.smt_transforms.smtlib_reader import SMTLIBReader
from automata_based_smt_solver.smt_transforms.symbol_coeff_normalizer import (
    SymbolCoeffNormalizer,
)


class Solver:
    def __init__(self) -> None:
        self.parser = SmtLibParser()
        self.reader = SMTLIBReader()

    def _rewrite_formula(self, formula: FNode) -> FNode:
        cnf = pysmt.rewritings.cnf(formula)
        negation_eliminated_cnf = NegationEliminator().walk(cnf)
        flattened_cnf = OrFlattener().walk(negation_eliminated_cnf)
        distributed = TimesDistributor().walk(flattened_cnf)
        normalized_coeff = SymbolCoeffNormalizer().walk(distributed)
        return CalculatingBracketExpander().walk(normalized_coeff)

    def _extract_data(self, cnf: FNode) -> list[list[FormulaData]]:
        result = []
        data_extractor = FormulaDataExtractor()
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
