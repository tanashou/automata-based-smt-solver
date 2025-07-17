from pysmt.shortcuts import And, Equals, Exists, ForAll, Int, Not, Or, Symbol, Times
from pysmt.typing import INT

from absmt.formula.rewritings import UniversalQFEliminator


def test_universal_qf_eliminator_basic():
    x = Symbol("x", INT)
    phi = Equals(x, Int(0))
    forall_formula = ForAll([x], phi)
    eliminator = UniversalQFEliminator()
    rewritten = eliminator.walk(forall_formula)
    expected = Not(Exists([x], Not(phi)))
    assert rewritten == expected


# Additional test: more complex body


def test_universal_qf_eliminator_complex():
    x = Symbol("x", INT)
    y = Symbol("y", INT)
    phi = And(Equals(x, y), Equals(x, Int(0)))
    forall_formula = ForAll([x], phi)
    eliminator = UniversalQFEliminator()
    rewritten = eliminator.walk(forall_formula)
    expected = Not(Exists([x], Not(phi)))
    assert rewritten == expected


def test_universal_qf_eliminator_and_predicates():
    x = Symbol("x", INT)
    y = Symbol("y", INT)
    p1 = Equals(x, y)
    p2 = Equals(x, Times(Int(2), y))
    phi = Or(p1, p2)
    forall_formula = ForAll([x], phi)
    eliminator = UniversalQFEliminator()
    rewritten = eliminator.walk(forall_formula)
    expected = Not(Exists([x], Not(phi)))
    assert rewritten == expected
