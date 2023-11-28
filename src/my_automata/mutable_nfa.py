from collections import defaultdict
from typing import Any
from automata.fa.nfa import NFA as BaseNFA


"""
The instance variables, such as 'states', in the NFA class from automata-lib are immutable.
I needed a mutable version of these variables to modify them during runtime, so I created a separate mutable object.
"""

SymbolT = str
NFAStateT = Any  # 入れ子になる可能性があるので、Anyにしておく
NFAPathT = defaultdict[SymbolT, set[NFAStateT]]
NFATransitionT = defaultdict[NFAStateT, NFAPathT]
InputPathListT = list[tuple[NFAStateT, NFAStateT, SymbolT]]


class MutableNFA:
    def __init__(
        self,
        *,
        states: set[NFAStateT],
        input_symbols: set[SymbolT],  # TODO: メモリを節約するため、正規表現にしたい
        transitions: NFATransitionT,
        initial_state: NFAStateT,
        final_states: set[NFAStateT],
    ) -> None:
        """Initialize a complete NFA."""

        self.__states = states
        self.__input_symbols = input_symbols
        self.__transitions = transitions
        self.__initial_state = initial_state
        self.__final_states = final_states

    @property
    def states(self) -> set[NFAStateT]:
        return self.__states

    @property
    def input_symbols(self) -> set[SymbolT]:
        return self.__input_symbols

    @property
    def transitions(self) -> NFATransitionT:
        return self.__transitions

    @property
    def initial_state(self) -> NFAStateT:
        return self.__initial_state

    @property
    def final_states(self) -> set[NFAStateT]:
        return self.__final_states

    def add_state(self, new_state: NFAStateT) -> None:
        self.__states.add(new_state)

    def add_states(self, new_states: set[NFAStateT]) -> None:
        self.__states.update(new_states)

    def add_input_symbol(self, new_input_symbol: str) -> None:
        self.__input_symbols.add(new_input_symbol)

    def add_transition(self, current_state: NFAStateT, symbol: str, next_state: NFAStateT) -> None:
        self.__transitions[current_state][symbol].add(next_state)

    def add_initial_state(self, new_initial_state: NFAStateT) -> None:
        self.__initial_state = new_initial_state

    def add_final_state(self, new_final_state: NFAStateT) -> None:
        self.__final_states.add(new_final_state)

    def get_next_states(self, current_state: NFAStateT, symbol: SymbolT) -> set[NFAStateT]:
        return self.__transitions[current_state][symbol]

    def show_diagram(self, path: str) -> None:
        base_nfa = BaseNFA(
            states=self.__states,
            input_symbols=self.__input_symbols,
            transitions=self.__transitions,
            initial_state=self.__initial_state,
            final_states=self.__final_states,
        )
        base_nfa.show_diagram(path=path)

    def dfs(self) -> bool:
        def get_neighbors(state: NFAStateT) -> set[NFAStateT]:
            neighbors = set()
            for symbol in self.input_symbols:
                neighbors.update(self.get_next_states(state, symbol))
            return neighbors

        stack: list[NFAStateT] = [self.initial_state]
        path_of_states: list[NFAStateT] = []  # 異なる入力で同じ状態に遷移する可能性があるため、状態のみを記録し、その後入力を探索する
        visited: set[NFAStateT] = set()  # TODO: このままでは毎回要素が集合にあるか探索する処理が必要になる。状態に番号を振って（辞書とか)、探索の計算量をO(1)にする。

        while stack:
            current_state = stack.pop()
            path_of_states.append(current_state)
            if current_state in self.final_states:
                print("reached to final state")
                print(path_of_states)
                return True

            visited.add(current_state)

            for neighbor_state in get_neighbors(current_state):
                if neighbor_state not in visited:
                    stack.append(neighbor_state)

        print("not reached to final state")
        return False
