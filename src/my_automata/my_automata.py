from automata.fa.nfa import NFA as BaseNFA
from collections import defaultdict


"""
The instance variables, such as 'states', in the NFA class from automata-lib are immutable.
I needed a mutable version of these variables to modify them during runtime, so I created a separate mutable object.
"""

SymbolT = str
NFAStateT = str
NFAPathT = defaultdict[str, set[NFAStateT]]
NFATransitionT = defaultdict[NFAStateT, NFAPathT]
InputPathListT = list[tuple[NFAStateT, NFAStateT, SymbolT]]


class MutableNFA:
    def __init__(
        self,
        *,
        states: set[NFAStateT],
        input_symbols: set[SymbolT],  # TODO: 全てのアルファベットを保存しておく必要はないので、正規表現などにしたい
        transitions: NFATransitionT,
        initial_state: NFAStateT,
        final_states: set[NFAStateT],
    ) -> None:
        """Initialize a complete NFA."""

        self.states = states
        self.input_symbols = input_symbols
        self.transitions = transitions
        self.initial_state = initial_state
        self.final_states = final_states

    def add_state(self, new_state: NFAStateT) -> None:
        self.states.add(new_state)

    def add_states(self, new_states: set[NFAStateT]) -> None:
        self.states.update(new_states)

    def add_input_symbol(self, new_input_symbol: str) -> None:
        self.input_symbols.add(new_input_symbol)

    def add_transition(self, current_state: NFAStateT, symbol: str, next_state: NFAStateT) -> None:
        self.transitions[current_state][symbol].add(next_state)

    def add_initial_state(self, new_initial_state: NFAStateT) -> None:
        self.initial_state = new_initial_state

    def add_final_state(self, new_final_state: NFAStateT) -> None:
        self.final_states.add(new_final_state)

    def find_transitions_from_keys(self, current_state: NFAStateT, symbol: SymbolT) -> set[NFAStateT]:
        return self.transitions[current_state][symbol]

    def __make_base_nfa(self) -> None:
        self.__base_nfa = BaseNFA(
            states=self.states,
            input_symbols=self.input_symbols,
            transitions=self.transitions,
            initial_state=self.initial_state,
            final_states=self.final_states,
        )

    def show_diagram(self, path: str) -> None:
        self.__make_base_nfa()
        self.__base_nfa.show_diagram(path=path)
