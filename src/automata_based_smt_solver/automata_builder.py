from itertools import product

from pysmt.fnode import FNode

from automata_based_smt_solver.automata.input_symbol import InputSymbol
from automata_based_smt_solver.automata.nfa import NFA
from automata_based_smt_solver.automata.state import INITIAL_STATE
from automata_based_smt_solver.formula.formula_data_extractor import (
    FormulaDataExtractor,
)
from automata_based_smt_solver.formula.formula_type import FormulaType


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
        self.has_not: bool = extracted.has_not
        self.create_all: bool = create_all  # for debug

        self.nfa = NFA()
        self.nfa.add_state(self.const)
        self.nfa.set_input_symbols(
            self._generate_input_symbols(all_vars_index_map, extracted.vars)
        )
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
                pass
            case FormulaType.LE:
                pass
            case FormulaType.BOOL:
                pass

    def eq_to_nfa(self) -> None:
        partial_sat = False

        while self.work_list:
            current_state = self.work_list.pop()
            for symbol in self.nfa.input_symbols:
                dot = self.dots[symbol]
                if (current_state - dot) & 1 == 0:
                    previous_state = (current_state - dot) // 2
                    previous_state = int(previous_state)
                    if str(previous_state) not in self.nfa.states:
                        self.nfa.add_state(str(previous_state))
                        self.work_list.append(previous_state)
                    self.nfa.add_transition(
                        str(previous_state), symbol, str(current_state)
                    )
                if current_state == -dot:
                    self.nfa.add_transition(INITIAL_STATE, symbol, str(current_state))
                    partial_sat = True
            # return after the for loop is finished.
            if partial_sat and not self.create_all:
                return

        # when the work_list is empty, building nfa is completed.
        self.__build_completed = True

    def leq_to_nfa(self) -> None:
        partial_sat = False

        while self.work_list:
            current_state = self.work_list.pop()
            for symbol in self.nfa.input_symbols:
                dot = self.dots[symbol]
                previous_state = (current_state - dot) // 2
                if str(previous_state) not in self.nfa.states:
                    self.nfa.add_state(str(previous_state))
                    self.work_list.append(previous_state)
                self.nfa.add_transition(str(previous_state), symbol, str(current_state))

                if current_state + dot >= 0:
                    self.nfa.add_transition(INITIAL_STATE, symbol, str(current_state))
                    partial_sat = True
            # return after the for loop is finished.
            if partial_sat and not self.create_all:
                return

        # when the work_list is empty, building nfa is completed.
        self.__build_completed = True
