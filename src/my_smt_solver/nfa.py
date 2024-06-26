from collections import deque, defaultdict
import itertools
from .type import SymbolT, NFAStateT, NFATransitionT
from .utils import apply_mask, decode_symbols_to_int, intersection_containing_wildcard

"""
The instance variables, such as 'states', in the NFA class from automata-lib are immutable.
I needed a mutable version of these variables to modify them during runtime, so I created a separate mutable object.
"""


class NFA:
    def __init__(
        self,
        *,
        states: set[NFAStateT],
        input_symbols: set[SymbolT],
        transitions: NFATransitionT,
        initial_state: NFAStateT,
        final_states: set[NFAStateT],
    ) -> None:
        self.__states = states
        self.__input_symbols = input_symbols
        self.__transitions = transitions
        self.__initial_state = initial_state
        self.__final_states = final_states

    def __str__(self) -> str:
        # Convert defaultdict to dict
        d = {k: dict(v) for k, v in self.transitions.items()}
        return f"states={self.states},\ninput_symbols={self.input_symbols},\ntransitions={d},\ninitial_state={self.initial_state},\nfinal_states={self.final_states}"

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
        from automata.fa.nfa import NFA as AutomataLibNFA

        base_nfa = AutomataLibNFA(
            states=self.__states,
            input_symbols=self.__input_symbols,
            transitions=self.__transitions,
            initial_state=self.__initial_state,
            final_states=self.__final_states,
        )
        base_nfa.show_diagram(path=path)

    def dfs_with_path(self) -> list[SymbolT]:
        # Define get_neighbors within dfs to include the symbol for the transition.
        def get_neighbors(state: NFAStateT) -> set[tuple[NFAStateT, SymbolT]]:
            neighbors = set()
            for symbol in self.input_symbols:
                next_states = self.get_next_states(state, symbol)
                for next_state in next_states:
                    neighbors.add((next_state, symbol))  # Include the symbol in the neighbor information
            return neighbors

        # Initialize the stack with the initial state.
        stack: deque[tuple[NFAStateT, list[SymbolT]]] = deque([(self.initial_state, [])])
        visited: set[NFAStateT] = {self.initial_state}

        while stack:
            current_state, path_of_symbols = stack.pop()

            if current_state in self.final_states:
                return path_of_symbols

            # Get neighbors only when necessary, i.e., when visiting the node.
            current_neighbors = get_neighbors(current_state)

            for neighbor_state, symbol in current_neighbors:
                if neighbor_state not in visited:
                    visited.add(neighbor_state)  # Move add operation here to avoid duplicate work
                    # Update new_symbols to include the symbol
                    new_symbols = path_of_symbols + [symbol]
                    stack.append((neighbor_state, new_symbols))

        return []

    def bfs_with_path(self) -> list[SymbolT]:
        # Define get_neighbors within dfs to include the symbol for the transition.
        def get_neighbors(state: NFAStateT) -> set[tuple[NFAStateT, SymbolT]]:
            neighbors = set()
            for symbol in self.input_symbols:
                next_states = self.get_next_states(state, symbol)
                for next_state in next_states:
                    neighbors.add((next_state, symbol))  # Include the symbol in the neighbor information
            return neighbors

        # Initialize the stack with the initial state.
        stack: deque[tuple[NFAStateT, list[SymbolT]]] = deque([(self.initial_state, [])])
        visited: set[NFAStateT] = {self.initial_state}

        while stack:
            current_state, path_of_symbols = stack.popleft()

            if current_state in self.final_states:
                return path_of_symbols

            # Get neighbors only when necessary, i.e., when visiting the node.
            current_neighbors = get_neighbors(current_state)

            for neighbor_state, symbol in current_neighbors:
                if neighbor_state not in visited:
                    visited.add(neighbor_state)  # Move add operation here to avoid duplicate work
                    # Update new_symbols to include the symbol
                    new_symbols = path_of_symbols + [symbol]
                    stack.append((neighbor_state, new_symbols))

        return []

    def intersection(self, other: "NFA") -> "NFA":
        initial_state = (self.initial_state, other.initial_state)
        nfa = NFA(
            states=set(),
            input_symbols=intersection_containing_wildcard(self.input_symbols, other.input_symbols),
            transitions=defaultdict(lambda: defaultdict(set)),
            initial_state=initial_state,
            final_states=set(),
        )
        work_list: list[NFAStateT] = [initial_state]

        if not nfa.input_symbols:
            raise ValueError("The given NFAs have no common input symbols")

        # create a mask for each nfa. The mask is used to apply wildcard to the input symbol.
        # use the first input symbol to create the mask
        mask1: list[bool] = [char != "*" for char in list(self.input_symbols)[0]]
        mask2: list[bool] = [char != "*" for char in list(other.input_symbols)[0]]

        while work_list:
            current_state1, current_state2 = work_list.pop()
            nfa.add_state((current_state1, current_state2))
            if current_state1 in self.final_states and current_state2 in other.final_states:
                nfa.add_final_state((current_state1, current_state2))
            for symbol in nfa.input_symbols:
                next_states1 = self.get_next_states(current_state1, apply_mask(symbol, mask1))
                next_states2 = other.get_next_states(current_state2, apply_mask(symbol, mask2))
                for next_state1, next_state2 in set(itertools.product(next_states1, next_states2)):
                    nfa.add_transition((current_state1, current_state2), symbol, (next_state1, next_state2))
                    if (next_state1, next_state2) not in nfa.states:
                        work_list.append((next_state1, next_state2))

        return nfa
