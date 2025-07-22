from dataclasses import dataclass

from .formula_type import FormulaType
from .quantifier_type import QuantifierType


@dataclass
class FormulaData:
    quantifier_type: QuantifierType
    quantifier_vars: list[str]
    coeffs: dict[str, int]
    const: int
    formula_type: FormulaType
