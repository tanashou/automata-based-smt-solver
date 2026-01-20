from pysmt.fnode import FNode
from pysmt.shortcuts import GT, LT, And, Equals, Not, Or, Symbol
from pysmt.typing import INT

from absmt.formula.rewritings.dnf_converter import DNFConverter


def formula_equal(f1, f2):
    if isinstance(f1, FNode) and isinstance(f2, FNode):
        if f1.is_and() and f2.is_and():
            return set(f1.args()) == set(f2.args())
        if f1.is_or() and f2.is_or():
            return set(f1.args()) == set(f2.args())
    return f1 == f2


class TestDNFConverterWithInts:
    def setup_method(self):
        # Generator ではなく Converter をインスタンス化
        self.converter = DNFConverter()

        # Integer variables
        x_var = Symbol("x", INT)
        y_var = Symbol("y", INT)
        z_var = Symbol("z", INT)
        k_var = Symbol("k", INT)

        # Atomic formulas based on integer arithmetic
        self.a = GT(x_var, y_var)
        self.b = LT(y_var, z_var)
        self.c = Equals(z_var, k_var)
        self.d = GT(k_var, x_var)
        self.x = Equals(x_var, y_var)  # Reusing x/y for different atoms
        self.y = LT(z_var, k_var)

    def assert_dnf_equals(self, formula, expected_dnf_set):
        # Converterを実行。戻り値は list[FNode] である前提。
        conjunctions: list[FNode] = self.converter.convert(formula)

        # リストを集合に変換して重複を排除し、順序を無視できるようにする
        actual_dnf_set = set(conjunctions)

        # 要素数が一致することを確認
        assert len(actual_dnf_set) == len(expected_dnf_set)

        # 期待される各連言が、結果の中に等価なものが存在することを確認
        for expected_formula in expected_dnf_set:
            assert any(
                formula_equal(expected_formula, actual_formula)
                for actual_formula in actual_dnf_set
            ), (
                f"Expected conjunction {expected_formula} not found in DNF result: "
                f"{actual_dnf_set}"
            )

    def test_single_literals(self):
        self.assert_dnf_equals(self.a, {self.a})
        self.assert_dnf_equals(Not(self.a), {Not(self.a)})

    def test_nested_ands(self):
        formula = And(And(self.a, self.b), And(self.c, self.d))
        expected = {And(self.a, self.b, self.c, self.d)}
        self.assert_dnf_equals(formula, expected)

    def test_nested_ors(self):
        formula = Or(Or(self.a, self.b), Or(self.c, self.d))
        expected = {self.a, self.b, self.c, self.d}
        self.assert_dnf_equals(formula, expected)

    def test_double_distribution(self):
        formula = And(Or(self.a, self.b), Or(self.c, self.d))
        expected = {
            And(self.a, self.c),
            And(self.a, self.d),
            And(self.b, self.c),
            And(self.b, self.d),
        }
        self.assert_dnf_equals(formula, expected)

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
        self.assert_dnf_equals(formula, expected)

    def test_deeply_nested_and_or(self):
        # Formula: (a|b&c) & (d|x&y)
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
        self.assert_dnf_equals(formula, expected)
