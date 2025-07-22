from pysmt.shortcuts import And, Equals, Exists, Int, Not, Or, Symbol
from pysmt.typing import INT

from absmt.formula.rewritings.double_negation_eliminator import DoubleNegationEliminator


def test_double_negation_basic():
    x = Symbol("x", INT)
    l1 = Equals(x, Int(1))
    formula = Not(Not(l1))
    eliminator = DoubleNegationEliminator()
    rewritten = eliminator.walk(formula)
    assert rewritten == l1


def test_double_negation_nested():
    x = Symbol("x", INT)
    y = Symbol("y", INT)
    l1 = Equals(x, Int(1))
    l2 = Equals(y, Int(2))
    formula = Not(Not(And(l1, Not(Not(l2)))))
    eliminator = DoubleNegationEliminator()
    rewritten = eliminator.walk(formula)
    # Should be And(l1, l2)
    assert rewritten.is_and()
    assert rewritten.arg(0) == l1
    assert rewritten.arg(1) == l2


def test_double_negation_or():
    x = Symbol("x", INT)
    y = Symbol("y", INT)
    l1 = Equals(x, Int(1))
    l2 = Equals(y, Int(2))

    formula = Not(Not(Or(Not(Not(l1)), l2)))
    eliminator = DoubleNegationEliminator()
    rewritten = eliminator.walk(formula)
    # Should be Or(l1, l2)
    assert rewritten.is_or()
    assert rewritten.arg(0) == l1
    assert rewritten.arg(1) == l2


def test_double_negation_with_exists():
    x = Symbol("x", INT)
    l1 = Equals(x, Int(1))
    formula = Not(Not(Exists([x], l1)))
    eliminator = DoubleNegationEliminator()
    rewritten = eliminator.walk(formula)
    # Should be Exists([x], l1)
    assert rewritten.is_exists()
    assert rewritten.quantifier_vars()[0] == x
    assert rewritten.arg(0) == l1
