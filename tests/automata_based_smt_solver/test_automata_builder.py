import pytest

from absmt.automata.msbf_alphabet_symbol import MSBFAlphabetSymbol
from absmt.automata_builder import AutomataBuilder
from absmt.formula.type import FormulaData, FormulaType


class TestAutomataBuilder:
    def setup_method(self):
        self.x = "x"
        self.y = "y"
        self.z = "z"
        self.all_vars = [self.x, self.y, self.z]
        self.all_var_index_map = {
            name: index for index, name in enumerate(self.all_vars)
        }

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
        used_vars = list(coeffs.keys())
        formula_data = FormulaData(
            coeffs=coeffs,
            const=0,  # const is not used in dot calculation
            formula_type=FormulaType.EQ,
            has_negation_before_bool_var=False,
        )
        builder = AutomataBuilder(
            formula_data, self.all_vars, self.all_var_index_map, used_vars
        )
        dots = builder._calc_dots(self.all_var_index_map)
        for bits, expected in expected_dots.items():
            assert dots[MSBFAlphabetSymbol(bits, mask)] == expected

    # x = 0 and y = 0 and x + y = 1 で unsat になるか
    def test_unsat(self):
        # x = 0
        coeffs = {self.x: 1}
        const = 0
        all_vars = [self.x, self.y]
        all_var_index_map = {var: index for index, var in enumerate(all_vars)}
        used_vars = [self.x]
        formula_data = FormulaData(
            coeffs=coeffs,
            const=const,
            formula_type=FormulaType.EQ,
            has_negation_before_bool_var=False,
        )
        builder1 = AutomataBuilder(
            formula_data, all_vars, all_var_index_map, used_vars, create_all=True
        )
        builder1.build_step()

        # y = 0
        coeffs = {self.y: 1}
        used_vars = [self.y]
        const = 0
        formula_data = FormulaData(
            coeffs=coeffs,
            const=const,
            formula_type=FormulaType.EQ,
            has_negation_before_bool_var=False,
        )
        builder2 = AutomataBuilder(
            formula_data, all_vars, all_var_index_map, used_vars, create_all=True
        )
        builder2.build_step()

        # x + y = 1
        coeffs = {self.x: 1, self.y: 1}
        used_vars = [self.x, self.y]
        const = 1
        formula_data = FormulaData(
            coeffs=coeffs,
            const=const,
            formula_type=FormulaType.EQ,
            has_negation_before_bool_var=False,
        )
        builder3 = AutomataBuilder(
            formula_data, all_vars, all_var_index_map, used_vars, create_all=True
        )
        builder3.build_step()

        intersection12 = builder1.nfa.intersection(builder2.nfa)
        intersection123 = intersection12.intersection(builder3.nfa)

        assert not intersection123.is_acceptable()

    # x + y = 1 と 2x + y = 0 でsat になるか
    def test_sat(self):
        # x + y = 1
        coeffs = {self.x: 1, self.y: 1}
        const = 1
        all_vars = [self.x, self.y]
        used_vars = [self.x, self.y]
        all_var_index_map = {var: index for index, var in enumerate(all_vars)}
        formula_data = FormulaData(
            coeffs=coeffs,
            const=const,
            formula_type=FormulaType.LE,
            has_negation_before_bool_var=False,
        )
        builder1 = AutomataBuilder(
            formula_data, all_vars, all_var_index_map, used_vars, create_all=True
        )
        builder1.build_step()

        # 2x + y = 0
        coeffs = {self.x: 2, self.y: 1}
        used_vars = [self.x, self.y]
        const = 0
        formula_data = FormulaData(
            coeffs=coeffs,
            const=const,
            formula_type=FormulaType.LE,
            has_negation_before_bool_var=False,
        )
        builder2 = AutomataBuilder(
            formula_data, all_vars, all_var_index_map, used_vars, create_all=True
        )
        builder2.build_step()

        intersection = builder1.nfa.intersection(builder2.nfa)

        assert intersection.is_acceptable()
