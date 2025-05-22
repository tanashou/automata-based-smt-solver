import pysmt.rewritings
from pysmt.fnode import FNode
from pysmt.rewritings import TimesDistributor
from pysmt.smtlib.parser import SmtLibParser

from automata_based_smt_solver.formula import DataExtractor, FormulaData
from automata_based_smt_solver.formula.rewritings import (
    CalculatingBracketExpander,
    NegationEliminator,
    OrFlattener,
    SymbolCoeffNormalizer,
)


class Solver:
    def __init__(self) -> None:
        self.parser = SmtLibParser()

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

    # ファイルはユーザー側がpysmt.parser を使って FNode に変換してもらう
    # 渡された FNode を AND でラップする
    def add(self, formula: FNode) -> None:
        pass
