import pytest
from pysmt.shortcuts import FALSE, TRUE, And, Not, Or, Symbol
from pysmt.typing import BOOL

# Using the import path you specified
from automata_based_smt_solver.formula.rewritings.dnf_generator import DNFGenerator


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
        assert set(self.dnf_generator.get_conjunctions(formula)) == expected

    def test_nested_ors(self):
        formula = Or(Or(self.a, self.b), Or(self.c, self.d))
        expected = {self.a, self.b, self.c, self.d}
        assert set(self.dnf_generator.get_conjunctions(formula)) == expected

    def test_double_distribution(self):
        formula = And(Or(self.a, self.b), Or(self.c, self.d))
        expected = {
            And(self.a, self.c),
            And(self.a, self.d),
            And(self.b, self.c),
            And(self.b, self.d),
        }
        assert set(self.dnf_generator.get_conjunctions(formula)) == expected

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
        assert set(self.dnf_generator.get_conjunctions(formula)) == expected

    def test_deeply_nested_and_or(self):
        # Formula: ( (a|b) & (c|d) ) | ( (x&y) | a )
        part1 = And(Or(self.a, self.b), Or(self.c, self.d))
        part2 = Or(And(self.x, self.y), self.a)
        formula = Or(part1, part2)

        expected = {
            And(self.a, self.c),
            And(self.a, self.d),
            And(self.b, self.c),
            And(self.b, self.d),
            And(self.x, self.y),
            self.a,  # Note that 'a' itself is a valid conjunction
        }
        assert set(self.dnf_generator.get_conjunctions(formula)) == expected

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
