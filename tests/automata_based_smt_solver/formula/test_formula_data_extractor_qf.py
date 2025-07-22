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
    assert result[0].quantifier_vars == {"x"}
    assert result[0].const == 5


def test_formula_data_extractor_qf_nested():
    x = Symbol("x", INT)
    y = Symbol("y", INT)
    z = Symbol("z", INT)
    # Nested exists and nested and/or
    # ∃x (x ≤ 1 and (y ≤ 2 or ∃z (z ≤ 3)))
    formula = Exists(
        [x], And(LE(x, Int(1)), Or(LE(y, Int(2)), Exists([z], LE(z, Int(3)))))
    )
    extractor = FormulaDataExtractorQF()
    result = extractor.extract_data(formula)
    # Top-level should be a list (from exists)
    assert isinstance(result, list)
    # The first element should be an 'and' node
    and_node = result[0]
    assert isinstance(and_node, dict)
    assert and_node["type"] == FormulaNodeType.AND
    # The second argument of 'and' should be an 'or' node
    or_node = and_node["args"][1]
    assert isinstance(or_node, dict)
    assert or_node["type"] == FormulaNodeType.OR
    # The last argument of 'or' should be a list from nested exists
    exists_node = or_node["args"][1]
    assert isinstance(exists_node, list)
    assert exists_node[0].quantifier_type == QuantifierType.EXISTS
    assert exists_node[0].quantifier_vars == {"x", "z"}
    assert exists_node[0].const == 3
