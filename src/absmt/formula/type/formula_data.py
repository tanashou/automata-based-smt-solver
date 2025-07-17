from dataclasses import dataclass

from absmt.formula.type import FormulaType, QuantifierType


@dataclass
class FormulaData:
    quantifier_type: QuantifierType
    quantifier_vars: list[str]
    coeffs: dict[str, int]
    const: int
    formula_type: FormulaType
