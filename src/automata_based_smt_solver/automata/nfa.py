# Copyright (c) 2016-2025 Caleb Evans
# This file is part of automata, licensed under the MIT License.
# See licenses/automata/LICENSE for full license information.
import contextlib
import copy
import os
from collections import defaultdict, deque
from itertools import chain
from typing import TYPE_CHECKING, TypeAlias

import pygraphviz as pgv

from automata_based_smt_solver.automata.msbf_alphabet import MSBFAlphabet
from automata_based_smt_solver.automata.msbf_alphabet_symbol import (
    MSBFAlphabetSymbol,
)
from automata_based_smt_solver.automata.state import NFAStateT, State

if TYPE_CHECKING:
    from collections.abc import Iterable

NFATransitionsT: TypeAlias = dict[State, dict[MSBFAlphabetSymbol, set[State]]]


class NFA:
    """NFA represents a custom NFA for use in the automata-based SMT solver.

    Attributes:
        _states (set[State]): Set of all states.
        _input_symbols (set[MSBFAlphabetSymbol]): Set of input symbols.
        _transitions (NFATransitionsT): Transition mapping.
        _initial_state (State): Starting state.
        _final_states (set[State]): Set of accepting states.

    """

    def __init__(
        self,
        states: set[State],
        input_symbols: MSBFAlphabet,
        transitions: NFATransitionsT,
        initial_state: State,
        final_states: set[State],
    ) -> None:
        """Initialize a NFA."""
        self._states = states
        self._input_symbols = input_symbols
        self._transitions = transitions
        self._initial_state = initial_state
        self._final_states = final_states

        if self._initial_state not in self._states:
            msg = "Initial state must be added to the set of states."
            raise ValueError(msg)

    def __str__(self) -> str:
        """Return a string representation of the NFA."""
        return (
            f"states={self.states},\n"
            f"input_symbols={self._input_symbols},\n"
            f"transitions={self.transitions},\n"
            f"initial_state={self.initial_state},\n"
            f"final_states={self.final_states}"
        )

    def __repr__(self) -> str:
        """Return a string representation of the NFA."""
        return f"NFA({self})"

    @property
    def states(self) -> set[State]:
        return self._states

    @property
    def input_symbols(self) -> MSBFAlphabet:
        return self._input_symbols

    @property
    def transitions(self) -> NFATransitionsT:
        return self._transitions

    @property
    def initial_state(self) -> State:
        return self._initial_state

    @property
    def final_states(self) -> set[State]:
        return self._final_states

    def add_state(self, new_state: State) -> None:
        self._states.add(new_state)

    def add_states(self, states: set[State]) -> None:
        self._states.update(states)

    def _set_initial_state(self) -> None:
        initial_state_name = "q0"
        self._initial_state = State(value=initial_state_name)
        self._states.add(self._initial_state)

    def _set_custom_initial_state(self, initial_state: State) -> None:
        """Set a custom initial state for the NFA. Only used in intersection."""
        self._states.remove(self._initial_state)
        self._initial_state = initial_state
        self._states.add(initial_state)

    def add_transition(
        self,
        start_state: State,
        symbol: MSBFAlphabetSymbol,
        end_state: State,
    ) -> None:
        self._transitions[start_state][symbol].add(end_state)

    def set_transitions(self, transitions: NFATransitionsT) -> None:
        self._transitions = transitions

    def add_final_state(self, new_final_state: State) -> None:
        self._final_states.add(new_final_state)

    def set_final_states(self, final_states: set[State]) -> None:
        self._final_states = final_states

    def get_next_states(
        self, current_state: State, input_symbol: MSBFAlphabetSymbol
    ) -> set[State]:
        """Get states reachable from current_state via input_symbol with wildcards.

        Args:
            current_state: Current state in the NFA.
            input_symbol: Input symbol to process (may contain wildcards).

        Returns:
            set[State]: Set of states reachable via the input symbol.

        """
        # Get all transitions from the current state
        state_transitions = self._transitions.get(current_state, {})
        if not state_transitions:
            return set()

        # Find all matching transitions
        result = set()
        for symbol, next_states in state_transitions.items():
            # Use MSBFAlphabetSymbol's __eq__ method which already handles wildcards
            if input_symbol == symbol:
                result.update(next_states)

        return result

    def accepts_input(self, input_str: list[MSBFAlphabetSymbol]) -> bool:
        """Check if the NFA accepts the given input sequence.

        Args:
            input_str: A list of MSBFAlphabetSymbol objects to process.

        Returns:
            bool: True if the NFA accepts the sequence, False otherwise.

        """
        # Start with initial state (no epsilon transitions)
        current_states = {self.initial_state}

        # Process each input symbol
        for symbol in input_str:
            next_states = set()
            for state in current_states:
                with contextlib.suppress(KeyError):
                    next_states.update(self.get_next_states(state, symbol))

            current_states = next_states

            # Early rejection if dead end
            if not current_states:
                return False

        # Accept if any current state is final
        return bool(current_states & self.final_states)

    def is_acceptable(self) -> bool:
        visited = set()
        stack = [self.initial_state]

        while stack:
            current_state = stack.pop()
            if current_state in visited:
                continue
            visited.add(current_state)
            if current_state in self.final_states:
                return True

            stack.extend(
                state
                for next_states in self.transitions.get(current_state, {}).values()
                for state in next_states
                if state not in visited
            )
        return False

    def show_diagram(
        self,
        input_str: str | None = None,
        path: str | os.PathLike | None = None,
    ) -> pgv.AGraph:
        raise NotImplementedError

    def intersection(self, other: "NFA") -> "NFA":  # noqa: C901
        new_states: set[State] = set()
        new_input_symbols: MSBFAlphabet = MSBFAlphabet.union_alphabet(
            self.input_symbols, other.input_symbols
        )
        new_transitions: NFATransitionsT = defaultdict(lambda: defaultdict(set))
        new_initial_state_value: tuple[NFAStateT, NFAStateT] = (
            self.initial_state.value,
            other.initial_state.value,
        )
        new_states.add(State(new_initial_state_value))

        queue: deque[tuple[NFAStateT, NFAStateT]] = deque()
        queue.append(new_initial_state_value)

        # Use a named constant for tuple length
        intersection_tuple_len = 2

        while queue:
            curr_state_value = queue.popleft()
            q_a, q_b = curr_state_value
            next_states_iterables: list[Iterable[State]] = []

            transitions_a = self.transitions.get(State(q_a), {})
            transitions_b = other.transitions.get(State(q_b), {})

            # Add all transitions moving over same input symbols
            for symbol in new_input_symbols.symbol_generator():
                end_states_a: set[State] = set()
                for key, dests in transitions_a.items():
                    if symbol == key:
                        end_states_a.update(dests)

                end_states_b: set[State] = set()
                for key, dests in transitions_b.items():
                    if symbol == key:
                        end_states_b.update(dests)

                if end_states_a and end_states_b:
                    state_dict = new_transitions[State(curr_state_value)]
                    product_states = [
                        State((state_a.value, state_b.value))
                        for state_a in end_states_a
                        for state_b in end_states_b
                    ]
                    state_dict[symbol].update(product_states)
                    next_states_iterables.append(product_states)

            for product_state in chain.from_iterable(next_states_iterables):
                if product_state not in new_states:
                    new_states.add(product_state)
                    if (
                        isinstance(product_state.value, tuple)
                        and len(product_state.value) == intersection_tuple_len
                    ):
                        queue.append(product_state.value)

        new_final_states: set[State] = {
            State((q_a.value, q_b.value))
            for q_a in self.final_states
            for q_b in other.final_states
        }

        return self.__class__(
            states=new_states,
            input_symbols=new_input_symbols,
            transitions=new_transitions,
            initial_state=State(new_initial_state_value),
            final_states=new_final_states,
        )

    @staticmethod
    def incremental_intersection(  # noqa: C901, PLR0912
        intersected_nfa_old: "NFA",
        n1_new: "NFA",
        n2_new: "NFA",
        delta_1_changes: NFATransitionsT,
        delta_2_changes: NFATransitionsT,
    ) -> "NFA":
        """Perform incremental intersection of two NFAs with changes."""
        intersection_tuple_len = 2
        intersected_nfa_new = copy.deepcopy(intersected_nfa_old)
        work_list: deque[tuple[State, MSBFAlphabetSymbol, State]] = deque()

        # seed N1 changes
        for q1_from, transitions_from_q1 in delta_1_changes.items():
            for symbol, to_states_set in transitions_from_q1.items():
                for q1_to in to_states_set:
                    for q2 in n2_new.states:
                        if (
                            q2 in n2_new.transitions
                            and symbol in n2_new.transitions[q2]
                        ):
                            for q2_to in n2_new.transitions[q2][symbol]:
                                intersected_state_from = State(
                                    (q1_from.value, q2.value)
                                )
                                intersected_state_to = State((q1_to.value, q2_to.value))
                                work_list.append(
                                    (
                                        intersected_state_from,
                                        symbol,
                                        intersected_state_to,
                                    )
                                )

        # seed N2 changes
        for q2_from, transitions_from_q2 in delta_2_changes.items():
            for symbol, to_states_set in transitions_from_q2.items():
                for q2_to in to_states_set:
                    for q1 in n1_new.states:
                        if (
                            q1 in n1_new.transitions
                            and symbol in n1_new.transitions[q1]
                        ):
                            for q1_to in n1_new.transitions[q1][symbol]:
                                intersected_state_from = State(
                                    (q1.value, q2_from.value)
                                )
                                intersected_state_to = State((q1_to.value, q2_to.value))
                                work_list.append(
                                    (
                                        intersected_state_from,
                                        symbol,
                                        intersected_state_to,
                                    )
                                )

        # --- Step 3: Processing loop (frontier exploration) ---
        while work_list:
            intersected_state_from, symbol, intersected_state_to = work_list.popleft()

            # Skip if transition already exists
            if (
                intersected_state_from in intersected_nfa_new.transitions
                and symbol in intersected_nfa_new.transitions[intersected_state_from]
                and intersected_state_to
                in intersected_nfa_new.transitions[intersected_state_from][symbol]
            ):
                continue

            # Add new transition to the product automaton
            if intersected_state_from not in intersected_nfa_new.transitions:
                intersected_nfa_new.transitions[intersected_state_from] = {}
            if symbol not in intersected_nfa_new.transitions[intersected_state_from]:
                intersected_nfa_new.transitions[intersected_state_from][symbol] = set()
            intersected_nfa_new.transitions[intersected_state_from][symbol].add(
                intersected_state_to
            )

            # If the destination state is new, add its transitions to the worklist
            if intersected_state_to not in intersected_nfa_new.states:
                intersected_nfa_new.states.add(intersected_state_to)

                # Check if it's an accepting state
                value = intersected_state_to.value
                if isinstance(value, tuple) and len(value) == intersection_tuple_len:
                    r1, r2 = value
                else:
                    msg = f"Invalid intersected state value: {value!r}"
                    raise ValueError(msg)

                if r1 in n1_new.final_states and r2 in n2_new.final_states:
                    intersected_nfa_new.final_states.add(intersected_state_to)

                # Propagate changes
                for next_symbol in n1_new.input_symbols.symbol_generator():
                    if (
                        State(r1) in n1_new.transitions
                        and next_symbol in n1_new.transitions[State(r1)]
                        and State(r2) in n2_new.transitions
                        and next_symbol in n2_new.transitions[State(r2)]
                    ):
                        for s1 in n1_new.transitions[State(r1)][next_symbol]:
                            for s2 in n2_new.transitions[State(r2)][next_symbol]:
                                next_intersected_state = State((s1.value, s2.value))
                                work_list.append(
                                    (
                                        intersected_state_to,
                                        next_symbol,
                                        next_intersected_state,
                                    )
                                )

        return intersected_nfa_new
