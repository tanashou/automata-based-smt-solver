# ruff: noqa: ANN201, ANN204, ANN001, ANN003, ARG002, D101, D107, D102
from pysmt.fnode import FNode
from pysmt.walkers import DagWalker


class CoefficientExtractor(DagWalker):
    def __init__(self):
        super().__init__()
        self._coeffs = {}

    @property
    def coeffs(self):
        return self._coeffs

    def walk_times(self, formula, args, **kwargs):
        if formula.arg(0).is_constant():
            coeff = formula.arg(0).constant_value()
            var = formula.arg(1)
            self._coeffs[var] = coeff
        elif formula.arg(1).is_constant():
            coeff = formula.arg(1).constant_value()
            var = formula.arg(0)
            self.coeffs[var] = coeff

    def walk(self, formula, **kwargs):
        if formula.is_times():
            return self.walk_times(formula, [], **kwargs)

        for subformula in formula.args():
            self.walk(subformula, **kwargs)
        return formula


def get_coeffs(f) -> dict[FNode, int]:
    """Get coefficients of a formula.

    If there is a Bool type variable, the coefficient is 0.
    """
    extractor = CoefficientExtractor()
    extractor.walk(f)
    coeffs = extractor.coeffs
    for var in f.get_free_variables():
        if var.get_type().is_bool_type():
            coeffs[var] = 0
        if var not in coeffs:
            coeffs[var] = 1
    return coeffs
