from typing import AbstractSet, Any, Mapping, NoReturn

AutomatonStateT = Any
AutomatonPathT = Mapping[str, Any]
AutomatonTransitionsT = Mapping[str, AutomatonPathT]

class NFA:
    initial_state: AutomatonStateT
    states: AbstractSet[AutomatonStateT]
    final_states: AbstractSet[AutomatonStateT]
    transitions: AutomatonTransitionsT
    input_symbols: AbstractSet[str]

    def __init__(self, initial_state: AutomatonStateT, states: AbstractSet[AutomatonStateT], final_states: AbstractSet[AutomatonStateT], transitions: AutomatonTransitionsT, input_symbols: AbstractSet[str]) -> NoReturn:
        self.initial_state = initial_state
        self.states = states
        self.final_states = final_states
        self.transitions = transitions
        self.input_symbols = input_symbols
