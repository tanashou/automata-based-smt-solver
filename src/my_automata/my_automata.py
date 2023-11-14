from typing import AbstractSet
from automata.fa.nfa import NFA as BaseNFA
import automata.fa.nfa as nfa


"""
The instance variables, such as 'states', in the NFA class from automata-lib are immutable by default.
I needed a mutable version of these variables to modify them during runtime, so I created a separate mutable object.
"""


# TODO: 作成したオートマトンが目的のものでなかった場合、再度途中から作り直す。この時、止まった時の変数の状態を保存しておく必要がある。ループ変数やwork_listの状態など
class MutableNFA:
    def __init__(
        self,
        *,
        states: AbstractSet[nfa.NFAStateT],
        input_symbols: AbstractSet[str],  # TODO: 全てのアルファベットを保存しておく必要はないので、正規表現などにしたい
        transitions: nfa.NFATransitionsT,
        initial_state: nfa.NFAStateT,
        final_states: AbstractSet[nfa.NFAStateT],
    ) -> None:
        """Initialize a complete NFA."""

        self.states = states
        self.input_symbols = input_symbols
        self.transitions = transitions
        self.initial_state = initial_state
        self.final_states = final_states

    def add_state(self, new_state: nfa.NFAStateT):
        self.states.add(new_state)

    def add_states(self, new_states: AbstractSet[nfa.NFAStateT]):
        self.states.update(new_states)

    def add_input_symbol(self, new_input_symbol: str):
        self.input_symbols.add(new_input_symbol)

    def add_transition(self, current_state: nfa.NFAStateT, symbol: str, next_state: nfa.NFAStateT):
        self.transitions.setdefault(current_state, {})
        self.transitions[current_state].setdefault(symbol, set())
        self.transitions[current_state][symbol].add(next_state)

    def add_initial_state(self, new_initial_state: nfa.NFAStateT):
        self.initial_state = new_initial_state

    def add_final_state(self, new_final_state: nfa.NFAStateT):
        self.final_states.add(new_final_state)

    # find a state that has the same transitions as the given state
    def find_transitions_from_keys(self, current_state: nfa.NFAStateT, symbol: str) -> AbstractSet[nfa.NFAStateT]:
        return self.transitions.get(current_state, {}).get(symbol, set())

    def __make_base_nfa(self):
        self.__base_nfa = BaseNFA(
            states=self.states,
            input_symbols=self.input_symbols,
            transitions=self.transitions,
            initial_state=self.initial_state,
            final_states=self.final_states,
        )

    def show_diagram(self, path=None):
        self.__make_base_nfa()
        self.__base_nfa.show_diagram(path=path)