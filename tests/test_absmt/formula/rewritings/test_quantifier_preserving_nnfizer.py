import pytest
from pysmt.shortcuts import And, Exists, ForAll, Implies, Int, Not, Or, Symbol
from pysmt.typing import INT

from absmt.formula.rewritings.quantifier_preserving_nnfizer import (
    QuantifierPreservingNNFizer,
)


@pytest.fixture
def nnfizer():
    return QuantifierPreservingNNFizer()


@pytest.fixture
def x():
    return Symbol("x", INT)


@pytest.fixture
def y():
    return Symbol("y", INT)


def test_boolean_connectives_int(nnfizer, x, y):
    l1 = x.Equals(Int(1))
    l2 = y.Equals(Int(2))
    formula1 = Not(And(l1, l2))
    expected1 = Or(Not(l1), Not(l2))
    result1 = nnfizer.convert(formula1)
    assert result1 == expected1, f"Expected {expected1}, got {result1}"

    formula2 = Not(Or(l1, l2))
    expected2 = And(Not(l1), Not(l2))
    result2 = nnfizer.convert(formula2)
    assert result2 == expected2, f"Expected {expected2}, got {result2}"

    formula3 = Implies(l1, l2)
    expected3 = Or(Not(l1), l2)
    result3 = nnfizer.convert(formula3)
    assert result3 == expected3, f"Expected {expected3}, got {result3}"


def test_quantifier_body_is_converted_int(nnfizer, x):
    p1 = x.Equals(Int(0))
    p2 = x.Equals(Int(10))
    formula = ForAll([x], Not(And(p1, p2)))
    expected = ForAll([x], Or(Not(p1), Not(p2)))
    result = nnfizer.convert(formula)
    assert result == expected, f"Expected {expected}, got {result}"


def test_negated_forall_is_preserved_int(nnfizer, x):
    p = x.Equals(Int(0))
    formula = Not(ForAll([x], p))
    expected = Not(ForAll([x], p))
    result = nnfizer.convert(formula)
    assert result == expected, f"Expected {expected}, got {result}"


def test_negated_exists_is_preserved_int(nnfizer, x):
    p = x.Equals(Int(0))
    formula = Not(Exists([x], p))
    expected = Not(Exists([x], p))
    result = nnfizer.convert(formula)
    assert result == expected, f"Expected {expected}, got {result}"


def test_negated_quantifier_with_complex_body_int(nnfizer, x):
    p1 = x.Equals(Int(0))
    p2 = x.Equals(Int(10))
    formula = Not(ForAll([x], Not(And(p1, p2))))
    expected = Not(ForAll([x], Or(Not(p1), Not(p2))))
    result = nnfizer.convert(formula)
    assert result == expected, f"Expected {expected}, got {result}"
