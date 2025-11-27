from dataclasses import dataclass

from .formula_type import FormulaType
from .quantifier_type import QuantifierType


@dataclass
class FormulaData:
    quantifier_type: QuantifierType
    quantifier_vars: set[str]
    coeffs: dict[str, int]
    const: int
    formula_type: FormulaType

    def all_vars_in_formula(self) -> set[str]:
        return self.coeffs.keys() | self.quantifier_vars

    def is_structurally_equal(self, other: "FormulaData") -> bool:
        if self.formula_type != other.formula_type:
            return False
        if self.const != other.const:
            return False
        if len(self.coeffs) != len(other.coeffs):
            return False

        self.coeff_values = sorted(self.coeffs.values())
        other_coeff_values = sorted(other.coeffs.values())
        return self.coeff_values == other_coeff_values
