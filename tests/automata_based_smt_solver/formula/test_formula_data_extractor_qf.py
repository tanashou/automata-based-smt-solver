from pysmt.shortcuts import LE, And, Exists, Int, Or, Symbol
from pysmt.typing import INT

from absmt.formula.formula_data_extractor_qf import FormulaDataExtractorQF
from absmt.formula.type import FormulaNodeType, QuantifierType


def test_formula_data_extractor_qf_and_or():
    x = Symbol("x", INT)
    y = Symbol("y", INT)
    formula = And(LE(x, Int(1)), LE(y, Int(2)))
    extractor = FormulaDataExtractorQF()
    result = extractor.extract_data(formula)
    assert isinstance(result, dict)
    assert result["type"] == FormulaNodeType.AND
    assert all(isinstance(arg, list) for arg in result["args"])

    formula_or = Or(LE(x, Int(1)), LE(y, Int(2)))
    result_or = extractor.extract_data(formula_or)
    assert isinstance(result_or, dict)
    assert result_or["type"] == FormulaNodeType.OR
    assert all(isinstance(arg, list) for arg in result_or["args"])


def test_formula_data_extractor_qf_exists():
    x = Symbol("x", INT)
    formula = Exists([x], LE(x, Int(5)))
    extractor = FormulaDataExtractorQF()
    result = extractor.extract_data(formula)
    # Should be a list containing FormulaData with quantifier_type EXISTS
    assert isinstance(result, list)
    assert result[0].quantifier_type == QuantifierType.EXISTS
    assert result[0].quantifier_vars == ["x"]
    assert result[0].const == 5
