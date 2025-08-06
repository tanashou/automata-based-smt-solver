from collections import defaultdict

from absmt.automata.msbf_alphabet import MSBFAlphabet
from absmt.automata.msbf_alphabet_symbol import MSBFAlphabetSymbol
from absmt.automata.nfa import NFA
from absmt.formula.type import FormulaData, FormulaType


class AutomataBuilder:
    def __init__(
        self,
        formula_data: FormulaData,
        all_vars: list[str],
        all_var_index_map: dict[str, int],
    ) -> None:
        self.formula_data: FormulaData = formula_data
        self.all_vars: list[str] = all_vars
        self.all_var_index_map: dict[str, int] = all_var_index_map

    def build(self) -> NFA:
        initial_state = "q0"
        final_state = self.formula_data.const

        nfa = NFA(
            states={initial_state, final_state},
            initial_state=initial_state,
            alphabet=MSBFAlphabet(self.all_vars, list(self.formula_data.used_vars())),
            transitions=defaultdict(lambda: defaultdict(set)),
            final_states={final_state},
        )

        dots = self._calc_dots(nfa.alphabet)
        work_list = [final_state]

        match self.formula_data.formula_type:
            case FormulaType.EQ:
                self._eq_to_nfa(nfa, work_list, dots)
            case FormulaType.LE:
                self._le_to_nfa(nfa, work_list, dots)

        return nfa

    def _calc_dots(self, alphabet: MSBFAlphabet) -> dict[MSBFAlphabetSymbol, int]:
        result = {}
        var_coef_index_pairs = [
            (coeff, self.all_var_index_map[var])
            for var, coeff in self.formula_data.coeffs.items()
        ]
        for symbol in alphabet.symbol_generator():
            result[symbol] = symbol.dot(var_coef_index_pairs)
        return result

    def _eq_to_nfa(
        self, nfa: NFA, work_list: list[int], dots: dict[MSBFAlphabetSymbol, int]
    ) -> None:
        while work_list:
            current_state = work_list.pop()
            for symbol in nfa.alphabet.symbol_generator():
                dot = dots[symbol]
                if (current_state - dot) & 1 == 0:
                    previous_state = (current_state - dot) // 2
                    if previous_state not in nfa.states:
                        nfa.add_state(previous_state)
                        work_list.append(previous_state)
                    nfa.add_transition(previous_state, symbol, current_state)
                if current_state == -dot:
                    nfa.add_transition(nfa.initial_state, symbol, current_state)

    def _le_to_nfa(
        self, nfa: NFA, work_list: list[int], dots: dict[MSBFAlphabetSymbol, int]
    ) -> None:
        while work_list:
            current_state = work_list.pop()
            for symbol in nfa.alphabet.symbol_generator():
                dot = dots[symbol]
                previous_state = (current_state - dot) // 2
                if previous_state not in nfa.states:
                    nfa.add_state(previous_state)
                    work_list.append(previous_state)
                nfa.add_transition(previous_state, symbol, current_state)

                if current_state + dot >= 0:
                    nfa.add_transition(nfa.initial_state, symbol, current_state)

    def projection(self, nfa: NFA) -> NFA:
        # TODO: Implement projection
        return nfa
