from dataclasses import dataclass

from pysmt.fnode import FNode

from automata_based_smt_solver.formula.type.formula_type import FormulaType


@dataclass
class FormulaData:
    coeffs: dict[FNode, int]
    const: int
    formula_type: FormulaType
    has_negation_before_bool_var: bool
