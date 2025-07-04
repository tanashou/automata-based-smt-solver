from dataclasses import dataclass

from absmt.formula.type.formula_type import FormulaType


@dataclass
class FormulaData:
    coeffs: dict[str, int]
    const: int
    formula_type: FormulaType
    has_negation_before_bool_var: bool
