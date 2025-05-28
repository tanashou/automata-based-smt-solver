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

    def test_generate_input_symbols(self):
        # x = 1
        coeffs = {self.x: 1}
        formula_data = FormulaData(
            coeffs=coeffs,
            vars={self.x},
            const=1,
            formula_type=FormulaType.EQ,
            has_negation_before_bool_var=False,
        )
        builder = AutomataBuilder(formula_data, self.all_vars, self.all_var_index_map)
        input_symbols = builder._generate_input_symbols(self.all_vars)
        mask = "100"
        expected_symbols = {InputSymbol("000", mask), InputSymbol("100", mask)}
        assert input_symbols == expected_symbols

    def test_generate_input_symbols_with_multiple_vars(self):
        # x + y = 2
        coeffs = {self.x: 1, self.y: 1}
        formula_data = FormulaData(
            coeffs=coeffs,
            vars={self.x, self.y},
            const=2,
            formula_type=FormulaType.EQ,
            has_negation_before_bool_var=False,
        )
        builder = AutomataBuilder(formula_data, self.all_vars, self.all_var_index_map)
        input_symbols = builder._generate_input_symbols(self.all_vars)
        mask = "110"
        expected_symbols = {
            InputSymbol("000", mask),
            InputSymbol("010", mask),
            InputSymbol("100", mask),
            InputSymbol("110", mask),
        }
        assert input_symbols == expected_symbols

    def test_generate_input_symbols_mask_and_symbols(self):
        # x + z = 3, all_vars = [x, y, z]
        coeffs = {self.x: 1, self.z: 1}
        formula_data = FormulaData(
            coeffs=coeffs,
            vars={self.x, self.z},
            const=3,
            formula_type=FormulaType.EQ,
            has_negation_before_bool_var=False,
        )
        builder = AutomataBuilder(formula_data, self.all_vars, self.all_var_index_map)
        input_symbols = builder._generate_input_symbols(self.all_vars)
        mask = "101"
        expected_symbols = {
            InputSymbol("000", mask),
            InputSymbol("001", mask),
            InputSymbol("100", mask),
            InputSymbol("101", mask),
        }
        assert input_symbols == expected_symbols
