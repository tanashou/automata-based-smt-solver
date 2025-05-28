import pytest
from pysmt.shortcuts import Symbol
from pysmt.typing import INT

from automata_based_smt_solver.automata.input_symbol import InputSymbol
from automata_based_smt_solver.automata_builder import AutomataBuilder
from automata_based_smt_solver.formula.type import FormulaData, FormulaType


class TestAutomataBuilder:
    def setup_method(self):
        self.x = Symbol("x", INT)
        self.y = Symbol("y", INT)
        self.z = Symbol("z", INT)
        self.all_vars = [self.x, self.y, self.z]
        self.all_var_index_map = {
            name: index for index, name in enumerate(self.all_vars)
        }

    @pytest.mark.parametrize(
        ("coeffs", "mask", "const", "expected_symbols"),
        [
            # x = 0
            (
                {"x": 1},
                "100",
                0,
                {"000", "100"},
            ),
            # x + y = 0
            (
                {"x": 1, "y": 1},
                "110",
                0,
                {"000", "010", "100", "110"},
            ),
            # x + z = 0
            (
                {"x": 1, "z": 1},
                "101",
                0,
                {"000", "001", "100", "101"},
            ),
            # x + y + z = 0
            (
                {"x": 1, "y": 1, "z": 1},
                "111",
                0,
                {"000", "001", "010", "011", "100", "101", "110", "111"},
            ),
        ],
    )
    def test_generate_input_symbols_parametrized(
        self, coeffs, mask, const, expected_symbols
    ):
        var_map = {"x": self.x, "y": self.y, "z": self.z}
        coeffs_sym = {var_map[k]: v for k, v in coeffs.items()}
        formula_data = FormulaData(
            coeffs=coeffs_sym,
            const=const,
            formula_type=FormulaType.EQ,
            has_negation_before_bool_var=False,
        )
        builder = AutomataBuilder(formula_data, self.all_vars, self.all_var_index_map)
        input_symbols = builder._generate_input_symbols(self.all_vars)
        expected = {InputSymbol(bits, mask) for bits in expected_symbols}
        assert input_symbols == expected

    @pytest.mark.parametrize(
        ("coeffs", "mask", "expected_dots"),
        [
            # x = 1
            # coeff vector: [1, 0, 0]
            (
                {"x": 1},
                "100",
                {
                    "000": 0,  # 0*1 + wildcard * 0 + wildcard * 0 = 0
                    "100": 1,  # 1*1 + wildcard * 0 + wildcard * 0 = 1
                },
            ),
            # x + y = 1, z is unused
            # coeff vector: [1, 1, 0]
            (
                {"x": 1, "y": 1},
                "110",
                {
                    "000": 0,  # 0*1 + 0*1 + wildcard * 0 = 0
                    "010": 1,  # 0*1 + 1*1 + wildcard * 0 = 1
                    "100": 1,  # 1*1 + 0*1 + wildcard * 0 = 1
                    "110": 2,  # 1*1 + 1*1 + wildcard * 0 = 2
                },
            ),
            # x - y = 0
            # coeff vector: [1, -1, 0]
            (
                {"x": 1, "y": -1},
                "110",
                {
                    "000": 0,  # 0*1 + 0*(-1) + wildcard * 0 = 0
                    "010": -1,  # 0*1 + 1*(-1) + wildcard * 0 = -1
                    "100": 1,  # 1*1 + 0*(-1) + wildcard * 0 = 1
                    "110": 0,  # 1*1 + 1*(-1) + wildcard * 0 = 0
                },
            ),
            # x + y + z = 3
            # coeff vector: [1, 1, 1]
            (
                {"x": 1, "y": 1, "z": 1},
                "111",
                {
                    "000": 0,  # 0*1 + 0*1 + 0*1 = 0
                    "001": 1,  # 0*1 + 0*1 + 1*1 = 1
                    "010": 1,  # 0*1 + 1*1 + 0*1 = 1
                    "011": 2,  # 0*1 + 1*1 + 1*1 = 2
                    "100": 1,  # 1*1 + 0*1 + 0*1 = 1
                    "101": 2,  # 1*1 + 0*1 + 1*1 = 2
                    "110": 2,  # 1*1 + 1*1 + 0*1 = 2
                    "111": 3,  # 1*1 + 1*1 + 1*1 = 3
                },
            ),
            # x + 5y - 3z = 0
            # coeff vector: [1, 5, -3]
            (
                {"x": 1, "y": 5, "z": -3},
                "111",
                {
                    "000": 0,  # 0*1 + 0*5 + 0*(-3) = 0
                    "001": -3,  # 0*1 + 0*5 + 1*(-3) = -3
                    "010": 5,  # 0*1 + 1*5 + 0*(-3) = 5
                    "011": 2,  # 0*1 + 1*5 + 1*(-3) = 2
                    "100": 1,  # 1*1 + 0*5 + 0*(-3) = 1
                    "101": -2,  # 1*1 + 0*5 + 1*(-3) = -2
                    "110": 6,  # 1*1 + 1*5 + 0*(-3) = 6
                    "111": 3,  # 1*1 + 1*5 + 1*(-3) = 3
                },
            ),
        ],
    )
    def test_calc_dots_parametrized(self, coeffs, mask, expected_dots):
        # Map string variable names to actual symbols
        var_map = {"x": self.x, "y": self.y, "z": self.z}
        coeffs_sym = {var_map[k]: v for k, v in coeffs.items()}
        formula_data = FormulaData(
            coeffs=coeffs_sym,
            const=0,  # const is not used in dot calculation
            formula_type=FormulaType.EQ,
            has_negation_before_bool_var=False,
        )
        builder = AutomataBuilder(formula_data, self.all_vars, self.all_var_index_map)
        dots = builder._calc_dots(self.all_var_index_map)
        for bits, expected in expected_dots.items():
            assert dots[InputSymbol(bits, mask)] == expected
