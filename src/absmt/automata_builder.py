from collections import defaultdict

from absmt.automata.msbf_alphabet import MSBFAlphabet
from absmt.automata.msbf_alphabet_symbol import MSBFAlphabetSymbol
from absmt.automata.nfa import NFA
from absmt.build_status import BuildStatus
from absmt.formula.type import FormulaData, FormulaType


# 1つのリテラルに対してnfaを作成していくクラス
class AutomataBuilder:
    def __init__(
        self,
        formula_data: FormulaData,
        all_vars: list[str],
        all_var_index_map: dict[str, int],
        used_vars: list[str],
    ) -> None:
        self.formula_data: FormulaData = formula_data
        initial_state = "q0"

        self.nfa = NFA(
            states={initial_state, self.formula_data.const},
            initial_state=initial_state,
            alphabet=MSBFAlphabet(all_vars, used_vars),
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
            case FormulaType.BOOL:
                if self.formula_data.has_negation_before_bool_var:
                    self.false_to_nfa()
                else:
                    self.true_to_nfa()

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

    def false_to_nfa(self) -> None:
        # add dead state
        dead_state = -1
        self.nfa.add_state(dead_state)
        # add final state
        final_state = self.formula_data.const
        self.nfa.add_state(final_state)

        # length of input_symbols is always 2 for boolean formulas
        for symbol in self.nfa.alphabet.symbol_generator():
            dot_value = self.dots[symbol]
            if dot_value == 1:
                self.nfa.add_transition(self.nfa.initial_state, symbol, final_state)
            else:
                self.nfa.add_transition(self.nfa.initial_state, symbol, dead_state)

            # add loop to dead state and final state
            self.nfa.add_transition(final_state, symbol, final_state)
            self.nfa.add_transition(dead_state, symbol, dead_state)

    def true_to_nfa(self) -> None:
        # add dead state
        dead_state = -1
        self.nfa.add_state(dead_state)
        # add final state
        final_state = self.formula_data.const
        self.nfa.add_state(final_state)

        # length of input_symbols is always 2 for boolean formulas
        for symbol in self.nfa.alphabet.symbol_generator():
            dot_value = self.dots[symbol]
            if dot_value == 0:
                self.nfa.add_transition(self.nfa.initial_state, symbol, final_state)
            else:
                self.nfa.add_transition(self.nfa.initial_state, symbol, dead_state)

            # add loop to dead state and final state
            self.nfa.add_transition(final_state, symbol, final_state)
            self.nfa.add_transition(dead_state, symbol, dead_state)
