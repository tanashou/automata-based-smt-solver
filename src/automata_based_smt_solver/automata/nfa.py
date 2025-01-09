# automata-lib v8.4.0 | MIT License | github.com/caleb531/automata
import os
from collections import defaultdict, deque
from itertools import chain, count, product, repeat
from typing import Any, TypeAlias

import pygraphviz as pgv
from automata.fa.nfa import NFA as BaseNFA  # noqa: N811

from automata_based_smt_solver.automata.input_symbol import EPSILON, InputSymbol
from automata_based_smt_solver.automata.state import State

NFAStateT: TypeAlias = Any  # Stateにしたい。
NFATransitionsT: TypeAlias = dict[NFAStateT, dict[InputSymbol, set[NFAStateT]]]


class NFA:
    id_counter: int = 0

    def __init__(
        self,
        *,
        states: set[NFAStateT],
        input_symbols: set[InputSymbol],
        transitions: NFATransitionsT,
        initial_state: NFAStateT,
        final_states: set[NFAStateT],
    ) -> None:
        self._id = NFA.id_counter
        self._states = states
        self._input_symbols = input_symbols
        self._transitions = transitions
        self._initial_state = initial_state
        self._final_states = final_states

        NFA.id_counter += 1

    def __str__(self) -> str:
        return (
            f"states={self.states},\n"
            f"input_symbols={self.input_symbols},\n"
            f"transitions={self.transitions},\n"
            f"initial_state={self.initial_state},\n"
            f"final_states={self.final_states}"
        )

    def __repr__(self) -> str:
        return f"NFA({self})"

    @property
    def states(self) -> set[NFAStateT]:
        return self._states

    @property
    def input_symbols(self) -> set[InputSymbol]:
        return self._input_symbols

    @property
    def transitions(self) -> NFATransitionsT:
        return self._transitions

    @property
    def initial_state(self) -> NFAStateT:
        return self._initial_state

    @property
    def final_states(self) -> set[NFAStateT]:
        return self._final_states

    @property
    def id(self) -> int:
        return self._id

    def add_state(self, new_state: NFAStateT) -> None:
        self._states.add(new_state)

    def add_input_symbol(self, new_input_symbol: InputSymbol) -> None:
        self._input_symbols.add(new_input_symbol)

    def add_transition(
        self, start_state: NFAStateT, symbol: InputSymbol, end_state: NFAStateT
    ) -> None:
        self._transitions[start_state][symbol].add(end_state)

    def add_initial_state(self, new_initial_state: NFAStateT) -> None:
        self._initial_state = new_initial_state

    def add_final_state(self, new_final_state: NFAStateT) -> None:
        self._final_states.add(new_final_state)

    def get_next_states(
        self, current_state: NFAStateT, symbol: InputSymbol
    ) -> set[NFAStateT]:
        return self._transitions[current_state][symbol]

    def show_diagram(
        self,
        input_str: str | None = None,
        path: str | os.PathLike | None = None,
    ) -> pgv.AGraph:
        base_nfa = BaseNFA(
            states=self.states,
            input_symbols=self.input_symbols,
            transitions=self.transitions,  # type: ignore[assignment]
            initial_state=self.initial_state,
            final_states=self.final_states,
        )
        return base_nfa.show_diagram(input_str=input_str, path=path)

    def dfs_with_path(self) -> list[InputSymbol]:
        # Define get_neighbors within dfs to include the symbol for the transition.
        def get_neighbors(state: NFAStateT) -> set[tuple[NFAStateT, InputSymbol]]:
            neighbors = set()
            for symbol in self.input_symbols:
                next_states = self.get_next_states(state, symbol)
                for next_state in next_states:
                    neighbors.add(
                        (next_state, symbol)
                    )  # Include the symbol in the neighbor information
            return neighbors

        # Initialize the stack with the initial state.
        stack: deque[tuple[NFAStateT, list[InputSymbol]]] = deque(
            [(self.initial_state, [])]
        )
        visited: set[NFAStateT] = {self.initial_state}

        while stack:
            current_state, path_of_symbols = stack.pop()

            if current_state in self.final_states:
                return path_of_symbols

            # Get neighbors only when necessary, i.e., when visiting the node.
            current_neighbors = get_neighbors(current_state)

            for neighbor_state, symbol in current_neighbors:
                if neighbor_state not in visited:
                    visited.add(
                        neighbor_state
                    )  # Move add operation here to avoid duplicate work
                    # Update new_symbols to include the symbol
                    new_symbols = [*path_of_symbols, symbol]
                    stack.append((neighbor_state, new_symbols))

        return []

    def bfs_with_path(self) -> list[InputSymbol]:
        # Define get_neighbors within dfs to include the symbol for the transition.
        def get_neighbors(state: NFAStateT) -> set[tuple[NFAStateT, InputSymbol]]:
            neighbors = set()
            for symbol in self.input_symbols:
                next_states = self.get_next_states(state, symbol)
                for next_state in next_states:
                    neighbors.add(
                        (next_state, symbol)
                    )  # Include the symbol in the neighbor information
            return neighbors

        # Initialize the stack with the initial state.
        stack: deque[tuple[NFAStateT, list[InputSymbol]]] = deque(
            [(self.initial_state, [])]
        )
        visited: set[NFAStateT] = {self.initial_state}

        while stack:
            current_state, path_of_symbols = stack.popleft()

            if current_state in self.final_states:
                return path_of_symbols

            # Get neighbors only when necessary, i.e., when visiting the node.
            current_neighbors = get_neighbors(current_state)

            for neighbor_state, symbol in current_neighbors:
                if neighbor_state not in visited:
                    visited.add(
                        neighbor_state
                    )  # Move add operation here to avoid duplicate work
                    # Update new_symbols to include the symbol
                    new_symbols = [*path_of_symbols, symbol]
                    stack.append((neighbor_state, new_symbols))

        return []

    @staticmethod
    def create_input_symbols_from_mask(mask: str) -> set[InputSymbol]:
        if not mask:
            return set()
        # Create options list based on mask bits: ["0","1"] or ["0"]
        options = [["0", "1"] if bit == "1" else ["0"] for bit in mask]

        # Generate all combinations as strings
        return {
            InputSymbol(value="".join(combo), mask=mask) for combo in product(*options)
        }

    def intersection(self, other: "NFA") -> "NFA":
        new_states = set()
        new_input_symbols = self.input_symbols | other.input_symbols
        new_transitions: NFATransitionsT = defaultdict(lambda: defaultdict(set))
        # new_initial_state を State にしたい
        new_initial_state = (self.initial_state, other.initial_state)

        queue: deque[NFAStateT] = deque()

        queue.append(new_initial_state)
        new_states.add(new_initial_state)

        while queue:
            curr_state = queue.popleft()
            q_a, q_b = curr_state
            # States we will consider adding to the queue
            next_states_iterables: list[list[NFAStateT]] = []

            # Get transition dict for states in self
            transitions_a = self.transitions.get(q_a, {})
            # Add epsilon transitions for first set of transitions
            epsilon_transitions_a = transitions_a.get(EPSILON)
            if epsilon_transitions_a is not None:
                state_dict = new_transitions.setdefault(curr_state, defaultdict(set))
                state_dict.setdefault(EPSILON, set()).update(
                    set(zip(epsilon_transitions_a, repeat(q_b)))
                )
                next_states_iterables.append(
                    list(zip(epsilon_transitions_a, repeat(q_b)))
                )

            # Get transition dict for states in other
            transitions_b = other.transitions.get(q_b, {})
            # Add epsilon transitions for second set of transitions
            epsilon_transitions_b = transitions_b.get(EPSILON)
            if epsilon_transitions_b is not None:
                state_dict = new_transitions.setdefault(curr_state, defaultdict(set))
                state_dict.setdefault(EPSILON, set()).update(
                    zip(repeat(q_a), epsilon_transitions_b, strict=False)
                )
                next_states_iterables.append(
                    list(zip(repeat(q_a), epsilon_transitions_b, strict=False))
                )

            # Add all transitions moving over same input symbols
            for symbol in new_input_symbols:
                end_states_a = transitions_a.get(symbol)
                end_states_b = transitions_b.get(symbol)

                if end_states_a is not None and end_states_b is not None:
                    state_dict = new_transitions.setdefault(
                        curr_state, defaultdict(set)
                    )
                    state_dict.setdefault(symbol, set()).update(
                        product(end_states_a, end_states_b)
                    )
                    next_states_iterables.append(
                        list(product(end_states_a, end_states_b))
                    )

            # Finally, try visiting every state we found.
            for product_state in chain.from_iterable(next_states_iterables):
                if product_state not in new_states:
                    new_states.add(product_state)
                    queue.append(product_state)

        new_final_states = {
            (state_a, state_b)
            for (state_a, state_b) in new_states
            if state_a in self.final_states and state_b in other.final_states
        }

        return self.__class__(
            states=new_states,
            input_symbols=new_input_symbols,
            transitions=new_transitions,
            initial_state=new_initial_state,
            final_states=new_final_states,
        )

    @staticmethod
    def _load_new_transition_dict(
        old_transition_dict: NFATransitionsT,
        new_transition_dict: NFATransitionsT,
    ) -> None:
        for state_a, transitions in old_transition_dict.items():
            if state_a not in new_transition_dict:
                new_transition_dict[state_a] = defaultdict(set)
            for symbol, states in transitions.items():
                new_transition_dict[state_a][symbol].update(states)

    @staticmethod
    def _get_state_maps(
        state_set_a: set[NFAStateT],
        state_set_b: set[NFAStateT],
        *,
        start: int = 0,
    ) -> tuple[dict[NFAStateT, int], dict[NFAStateT, int]]:
        """Generate state map dicts from given sets.

        Useful when the state set has to
        be a union of the state sets of component FAs.

        同じ名前の状態が複数ある場合、区別しないといけないので、番号をつけている。
        fixme: union の intersection は違う状態に同じ番号がついてしまう。避けたい。
        """
        state_name_counter = count(start)

        state_map_a = dict(zip(state_set_a, state_name_counter, strict=False))
        state_map_b = dict(zip(state_set_b, state_name_counter, strict=False))

        return (state_map_a, state_map_b)

    def union(self, other: "NFA") -> "NFA":
        """Return an NFA which accepts the union of L1 and L2.

        Given two NFAs, M1 and M2, which accept the languages
        L1 and L2 respectively, returns an NFA which accepts
        the union of L1 and L2.
        """
        initial_state = State("")  # 特別な初期状態。
        new_states = {State(state.state_value, self.id) for state in self.states} | {
            State(state.state_value, other.id) for state in other.states
        }
        new_states.add(initial_state)
        new_transitions: NFATransitionsT = {}

        # Connect new initial state to both branch
        new_transitions[initial_state] = {
            EPSILON: {self.initial_state, other.initial_state}
        }
        new_transitions.update(self.transitions)
        new_transitions.update(other.transitions)

        new_final_states = self.final_states | other.final_states
        new_input_symbols = self.input_symbols | other.input_symbols

        return self.__class__(
            states=new_states,
            input_symbols=new_input_symbols,
            transitions=new_transitions,
            initial_state=initial_state,
            final_states=new_final_states,
        )

    # def concatenate(self, other: "NFA") -> "NFA":
    #     pass
