import pytest
from pysmt.fnode import FNode
from pysmt.shortcuts import FALSE, TRUE, And, Not, Or, Symbol
from pysmt.typing import BOOL

from automata_based_smt_solver.formula.rewritings.dnf_generator import DNFGenerator


def formula_equal(f1, f2):
    """Check if two formulas are mathematically equal.

    Ignores argument order for And/Or. Accepts pysmt formula objects.
    """
    if isinstance(f1, FNode) and isinstance(f2, FNode):
        if f1.is_and() and f2.is_and():
            return set(f1.args()) == set(f2.args())
        if f1.is_or() and f2.is_or():
            return set(f1.args()) == set(f2.args())
    return f1 == f2


class TestDNFGenerator:
    def setup_method(self):
        self.dnf_generator = DNFGenerator()
        self.a = Symbol("bv_a", BOOL)
        self.b = Symbol("bv_b", BOOL)
        self.c = Symbol("bv_c", BOOL)
        self.d = Symbol("bv_d", BOOL)
        self.x = Symbol("bv_x", BOOL)
        self.y = Symbol("bv_y", BOOL)

    def test_single_literals(self):
        # Test a single positive literal
        assert set(self.dnf_generator.get_conjunctions(self.a)) == {self.a}
        # Test a single negative literal
        assert set(self.dnf_generator.get_conjunctions(Not(self.a))) == {Not(self.a)}

    def test_constants(self):
        # TRUE is a DNF with one conjunction: TRUE
        assert set(self.dnf_generator.get_conjunctions(TRUE())) == {TRUE()}
        # FALSE is an empty DNF (no conjunctions)
        assert set(self.dnf_generator.get_conjunctions(FALSE())) == set()

    def test_nested_ands(self):
        formula = And(And(self.a, self.b), And(self.c, self.d))
        expected = {And(self.a, self.b, self.c, self.d)}
        actual = set(self.dnf_generator.get_conjunctions(formula))
        assert len(actual) == len(expected)
        for e in expected:
            assert any(formula_equal(e, a) for a in actual)

    def test_nested_ors(self):
        formula = Or(Or(self.a, self.b), Or(self.c, self.d))
        expected = {self.a, self.b, self.c, self.d}
        actual = set(self.dnf_generator.get_conjunctions(formula))
        assert len(actual) == len(expected)
        for e in expected:
            assert any(formula_equal(e, a) for a in actual)

    def test_double_distribution(self):
        formula = And(Or(self.a, self.b), Or(self.c, self.d))
        expected = {
            And(self.a, self.c),
            And(self.a, self.d),
            And(self.b, self.c),
            And(self.b, self.d),
        }
        actual = set(self.dnf_generator.get_conjunctions(formula))
        assert len(actual) == len(expected)
        for e in expected:
            assert any(formula_equal(e, a) for a in actual)

    def test_complex_nested_formula(self):
        # Formula: (a & (b|c)) | ((x|y) & d)
        f1 = And(self.a, Or(self.b, self.c))
        f2 = And(Or(self.x, self.y), self.d)
        formula = Or(f1, f2)
        expected = {
            And(self.a, self.b),
            And(self.a, self.c),
            And(self.x, self.d),
            And(self.y, self.d),
        }
        actual = set(self.dnf_generator.get_conjunctions(formula))
        assert len(actual) == len(expected)
        for e in expected:
            assert any(formula_equal(e, a) for a in actual)

    def test_deeply_nested_and_or(self):
        # Formula: (a|b&c) & (d|e&f)
        part1 = Or(self.a, And(self.b, self.c))
        part2 = Or(self.d, And(self.x, self.y))
        formula = And(part1, part2)
        # Expected DNF: (a & d) | (a & x & y) | (b & c & d) | (b & c & x & y)
        expected = {
            And(self.a, self.d),
            And(self.a, self.x, self.y),
            And(self.b, self.c, self.d),
            And(self.b, self.c, self.x, self.y),
        }
        actual = set(self.dnf_generator.get_conjunctions(formula))
        assert len(actual) == len(expected)
        for e in expected:
            assert any(formula_equal(e, a) for a in actual)

    def test_generator_exhaustion(self):
        expected_conjunctions_count = 4
        formula = And(Or(self.a, self.b), Or(self.c, self.d))
        conjunction_gen = self.dnf_generator.get_conjunctions(formula)
        # Consume it completely
        results = list(conjunction_gen)
        assert len(results) == expected_conjunctions_count
        # Now, calling next should raise StopIteration
        with pytest.raises(StopIteration):
            next(conjunction_gen)

    def test_generator_is_lazy(self):
        formula = And(Or(self.a, self.b), Or(self.c, self.d))
        expected_conjunctions = {
            And(self.a, self.c),
            And(self.a, self.d),
            And(self.b, self.c),
            And(self.b, self.d),
        }

        # Get the generator object, do not consume it yet
        conjunction_gen = self.dnf_generator.get_conjunctions(formula)

        # Pull items one by one and check state at each step
        results = set()

        results.add(next(conjunction_gen))
        assert len(results) == 1

        results.add(next(conjunction_gen))
        assert len(results) == 2

        results.add(next(conjunction_gen))
        assert len(results) == 3

        results.add(next(conjunction_gen))
        assert len(results) == 4

        # After pulling all items, the set of results should match the expected DNF
        assert results == expected_conjunctions

        # The next call should now fail, proving exhaustion
        with pytest.raises(StopIteration):
            next(conjunction_gen)
