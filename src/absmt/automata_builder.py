from collections import defaultdict

from absmt.automata.msbf_alphabet import MSBFAlphabet
from absmt.automata.msbf_alphabet_symbol import MSBFAlphabetSymbol
from absmt.automata.nfa import NFA
from absmt.build_status import BuildStatus
from absmt.formula.type import FormulaData, FormulaType


class AutomataBuilder:
    def __init__(
        self,
        formula_data: FormulaData,
        all_vars: list[str],
        all_var_index_map: dict[str, int],
    ) -> None:
        self.formula_data: FormulaData = formula_data
        initial_state = "q0"

        self.nfa = NFA(
            states={initial_state, self.formula_data.const},
            initial_state=initial_state,
            alphabet=MSBFAlphabet(all_vars, list(self.formula_data.used_vars())),
            transitions=defaultdict(lambda: defaultdict(set)),
            final_states={self.formula_data.const},
        )

        self.dots: dict[MSBFAlphabetSymbol, int] = self._calc_dots(all_var_index_map)
        self.work_list = [self.formula_data.const]

        self._build_status = BuildStatus.UNTOUCHED

    @property
    def build_status(self) -> BuildStatus:
        return self._build_status

    def _calc_dots(
        self, all_var_index_map: dict[str, int]
    ) -> dict[MSBFAlphabetSymbol, int]:
        result = {}
        var_coef_index_pairs = [
            (coeff, all_var_index_map[var])
            for var, coeff in self.formula_data.coeffs.items()
        ]
        for symbol in self.nfa.alphabet.symbol_generator():
            result[symbol] = symbol.dot(var_coef_index_pairs)
        return result

    def build(self) -> None:
        match self.formula_data.formula_type:
            case FormulaType.EQ:
                self.eq_to_nfa()
            case FormulaType.LE:
                self.le_to_nfa()

    def eq_to_nfa(self) -> None:
        while self.work_list:
            current_state = self.work_list.pop()
            for symbol in self.nfa.alphabet.symbol_generator():
                dot = self.dots[symbol]
                if (current_state - dot) & 1 == 0:
                    previous_state = (current_state - dot) // 2
                    if previous_state not in self.nfa.states:
                        self.nfa.add_state(previous_state)
                        self.work_list.append(previous_state)
                    self.nfa.add_transition(previous_state, symbol, current_state)
                if current_state == -dot:
                    self.nfa.add_transition(
                        self.nfa.initial_state, symbol, current_state
                    )

    def le_to_nfa(self) -> None:
        while self.work_list:
            current_state = self.work_list.pop()
            for symbol in self.nfa.alphabet.symbol_generator():
                dot = self.dots[symbol]
                previous_state = (current_state - dot) // 2
                if previous_state not in self.nfa.states:
                    self.nfa.add_state(previous_state)
                    self.work_list.append(previous_state)
                self.nfa.add_transition(previous_state, symbol, current_state)

                if current_state + dot >= 0:
                    self.nfa.add_transition(
                        self.nfa.initial_state, symbol, current_state
                    )
