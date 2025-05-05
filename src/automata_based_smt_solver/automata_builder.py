from itertools import product

from pysmt.fnode import FNode

from automata_based_smt_solver.automata.input_symbol import InputSymbol
from automata_based_smt_solver.automata.nfa import NFA
from automata_based_smt_solver.automata.state import INITIAL_STATE
from automata_based_smt_solver.smt_transforms.formula_data_extractor import (
    FormulaDataExtractor,
)
from automata_based_smt_solver.smt_transforms.formula_type import FormulaType


# 1つのリテラルに対してnfaを作成していくクラス
class AutomataBuilder:
    def __init__(
        self,
        formula: FNode,
        all_vars_index_map: dict[str, int],
        *,
        create_all: bool = False,
    ) -> None:
        extracted = FormulaDataExtractor().extract(formula)

        self.coeffs: dict[FNode, int] = extracted.coeffs
        self.const: int = extracted.const
        self.formula_type: FormulaType = extracted.formula_type
        self.has_negation_before_bool_var: bool = extracted.has_negation_before_bool_var
        self.create_all: bool = create_all  # for debug

        self.nfa = NFA()
        self.nfa.add_state(self.const)
        self.nfa.set_input_symbols(
            self._generate_input_symbols(all_vars_index_map, extracted.vars)
        )
        self.nfa.set_initial_state(INITIAL_STATE)
        self.nfa.add_final_state(self.const)

        self.dots: dict[InputSymbol, int] = self._calc_dots(all_vars_index_map)
        self.work_list = [self.const]
        self.__build_completed = False

    @property
    def build_completed(self) -> bool:
        return self.__build_completed

    def _generate_input_symbols(
        self, all_vars_index_map: dict[str, int], declared_vars: set[str]
    ) -> set[InputSymbol]:
        all_sorted_vars = [
            var
            for var, _ in sorted(all_vars_index_map.items(), key=lambda item: item[1])
        ]
        mask = "".join("1" if var in declared_vars else "0" for var in all_sorted_vars)
        choices = [("0", "1") if ch == "1" else ("0",) for ch in mask]
        symbols = {"".join(bits) for bits in product(*choices)}
        return {InputSymbol(symbol, mask) for symbol in symbols}

    def _calc_dots(self, all_vars_index_map: dict[str, int]) -> dict[InputSymbol, int]:
        result = {}
        var_coef_index_pairs = [
            (coeff, all_vars_index_map[str(var)]) for var, coeff in self.coeffs.items()
        ]
        for symbol in self.nfa.input_symbols:
            result[symbol] = symbol.dot(var_coef_index_pairs)
        return result

    def next(self) -> None:
        # yeild を使って 各種nfa変換関数を呼び出す
        match self.formula_type:
            case FormulaType.EQ:
                self.eq_to_nfa()
            case FormulaType.LE:
                self.le_to_nfa()
            case FormulaType.BOOL:
                if self.has_negation_before_bool_var:
                    self.false_to_nfa()
                else:
                    self.true_to_nfa()

    def eq_to_nfa(self) -> None:
        partial_sat = False

        while self.work_list:
            current_state_val = self.work_list.pop()
            for symbol in self.nfa.input_symbols:
                dot = self.dots[symbol]
                if (current_state_val - dot) & 1 == 0:
                    previous_state_val = (current_state_val - dot) // 2
                    if not self.nfa.contains_state(previous_state_val):
                        self.nfa.add_state(previous_state_val)
                        self.work_list.append(previous_state_val)
                    self.nfa.add_transition(
                        previous_state_val, symbol, current_state_val
                    )
                if current_state_val == -dot:
                    self.nfa.add_transition(INITIAL_STATE, symbol, current_state_val)
                    partial_sat = True
            # return after the for loop is finished.
            if partial_sat and not self.create_all:
                return

        # when the work_list is empty, building nfa is completed.
        self.__build_completed = True

    def le_to_nfa(self) -> None:
        partial_sat = False

        while self.work_list:
            current_state_val = self.work_list.pop()
            for symbol in self.nfa.input_symbols:
                dot = self.dots[symbol]
                previous_state_val = (current_state_val - dot) // 2
                if not self.nfa.contains_state(previous_state_val):
                    self.nfa.add_state(previous_state_val)
                    self.work_list.append(previous_state_val)
                self.nfa.add_transition(previous_state_val, symbol, current_state_val)

                if current_state_val + dot >= 0:
                    self.nfa.add_transition(INITIAL_STATE, symbol, current_state_val)
                    partial_sat = True
            # return after the for loop is finished.
            if partial_sat and not self.create_all:
                return

        # when the work_list is empty, building nfa is completed.
        self.__build_completed = True

    def false_to_nfa(self) -> None:
        # 1 を含むsymbolでfinal stateに遷移するnfaを作成する。
        final_state = self.const
        for symbol in self.nfa.input_symbols:
            dot_value = self.dots[symbol]
            if dot_value == 1:  # if the input_symbol includes 1
                self.nfa.add_transition(INITIAL_STATE, symbol, final_state)
                break

        self.__build_completed = True

    def true_to_nfa(self) -> None:
        # 0 を含むsymbolでfinal stateに遷移するnfaを作成する。
        final_state = self.const
        for symbol in self.nfa.input_symbols:
            dot_value = self.dots[symbol]
            if dot_value == 0:
                self.nfa.add_transition(INITIAL_STATE, symbol, final_state)
                break

        self.__build_completed = True
