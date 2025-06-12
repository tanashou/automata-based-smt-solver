# Copyright (c) 2016-2025 Caleb Evans
# This file is part of automata, licensed under the MIT License.
# See licenses/automata/LICENSE for full license information.
import contextlib
import os
from collections import defaultdict, deque
from itertools import chain, product
from typing import TYPE_CHECKING, TypeAlias, cast

import pygraphviz as pgv
from automata.fa.nfa import NFA as BaseNFA  # noqa: N811

from automata_based_smt_solver.automata.input_symbol import EPSILON, InputSymbol
from automata_based_smt_solver.automata.state import NFAStateT, State

if TYPE_CHECKING:
    from collections.abc import Iterable

NFATransitionsT: TypeAlias = dict[State, dict[InputSymbol, set[State]]]


class NFA:
    """NFA represents a custom NFA for use in the automata-based SMT solver.

    Attributes:
        _id (int): Unique identifier for the NFA.
        _states (set[State]): Set of all states.
        _input_symbols (set[InputSymbol]): Set of input symbols.
        _transitions (NFATransitionsT): Transition mapping.
        _initial_state (State): Starting state.
        _final_states (set[State]): Set of accepting states.

    """

    def __init__(self) -> None:
        """Initialize a NFA."""
        self._states: set[State] = set()
        self._input_symbols: set[InputSymbol] = set()
        self._transitions: NFATransitionsT = cast(
            NFATransitionsT, defaultdict(lambda: defaultdict(set))
        )
        self._set_initial_state()
        self._states.add(self._initial_state)
        self._final_states: set[State] = set()

    def __str__(self) -> str:
        """Return a string representation of the NFA."""
        return (
            f"states={self.states},\n"
            f"input_symbols={self.input_symbols},\n"
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
    def input_symbols(self) -> set[InputSymbol]:
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

    def add_input_symbol(self, new_input_symbol: InputSymbol) -> None:
        self._input_symbols.add(new_input_symbol)

    def set_input_symbols(self, input_symbols: set[InputSymbol]) -> None:
        self._input_symbols = input_symbols

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
        symbol: InputSymbol,
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
        self, current_state: State, input_symbol: InputSymbol
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
            # Use InputSymbol's __eq__ method which already handles wildcards
            if input_symbol == symbol:
                result.update(next_states)

        return result

    def contains_state(self, state: State) -> bool:
        return state in self.states

    def accepts_input(self, input_str: list[InputSymbol]) -> bool:
        """Check if the NFA accepts the given input sequence.

        Args:
            input_str: A list of InputSymbol objects to process.

        Returns:
            bool: True if the NFA accepts the sequence, False otherwise.

        """
        # Start with initial state and follow epsilon transitions
        current_states = self._follow_epsilon_transitions({self.initial_state})

        # Process each input symbol
        for symbol in input_str:
            next_states = set()
            for state in current_states:
                with contextlib.suppress(KeyError):
                    next_states.update(self.get_next_states(state, symbol))

            # Follow epsilon transitions from new states
            current_states = self._follow_epsilon_transitions(next_states)

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

    def _follow_epsilon_transitions(self, states: set[State]) -> set[State]:
        """Follow all epsilon transitions from given states."""
        result = set(states)
        stack = list(states)
        visited = set(stack)

        while stack:
            state = stack.pop()
            try:
                epsilon_states = self.get_next_states(state, EPSILON)
                for eps_state in epsilon_states:
                    if eps_state not in visited:
                        visited.add(eps_state)
                        stack.append(eps_state)
                        result.add(eps_state)
            except KeyError:
                continue

        return result

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

    @staticmethod
    def create_input_symbols_from_mask(mask: str) -> set[InputSymbol]:
        if not mask:
            return set()
        # Create options list based on mask bits: ["0","1"] or ["0"]
        options = [["0", "1"] if bit == "1" else ["0"] for bit in mask]

        # Generate all combinations as strings
        return {
            InputSymbol(bin_value="".join(combo), bin_mask=mask)
            for combo in product(*options)
        }

    def _input_symbol_intersection(
        self, s1: set[InputSymbol], s2: set[InputSymbol]
    ) -> set[InputSymbol]:
        tmp = s1 | s2
        mask = 0
        # 全ての input symbol でワイルドカードの桁を探す
        for symbol in tmp:
            mask |= symbol.mask
        bin_length = tmp.pop().bin_length
        mask_str = bin(mask)[2:].zfill(bin_length)
        choices = [("0", "1") if ch == "1" else ("0",) for ch in mask_str]
        symbols = {"".join(bits) for bits in product(*choices)}
        return {InputSymbol(symbol, mask_str) for symbol in symbols}

    def intersection(self, other: "NFA") -> "NFA":  # noqa: C901, PLR0912
        result = self.__class__()
        new_states: set[State] = set()
        new_input_symbols: set[InputSymbol] = self._input_symbol_intersection(
            self.input_symbols, other.input_symbols
        )
        new_transitions: NFATransitionsT = defaultdict(lambda: defaultdict(set))

        new_initial_state_value: tuple[NFAStateT, NFAStateT] = (
            self.initial_state.value,
            other.initial_state.value,
        )

        result._set_custom_initial_state(State(new_initial_state_value))  # noqa: SLF001

        queue: deque[tuple[NFAStateT, NFAStateT]] = deque()
        queue.append(new_initial_state_value)

        while queue:
            curr_state_value = queue.popleft()
            q_a, q_b = curr_state_value
            # States we will consider adding to the queue
            next_states_iterables: list[Iterable[State]] = []

            # Get transition dict for states in self
            transitions_a = self.transitions.get(State(q_a), {})
            # Add epsilon transitions for first set of transitions
            epsilon_transitions_a = transitions_a.get(EPSILON)
            if epsilon_transitions_a is not None:
                state_dict = new_transitions[State(curr_state_value)]
                new_states_a = [
                    State((state_a.value, q_b)) for state_a in epsilon_transitions_a
                ]
                state_dict[EPSILON].update(new_states_a)
                next_states_iterables.append(new_states_a)

            # Get transition dict for states in other
            transitions_b = other.transitions.get(State(q_b), {})
            # Add epsilon transitions for second set of transitions
            epsilon_transitions_b = transitions_b.get(EPSILON)
            if epsilon_transitions_b is not None:
                state_dict = new_transitions[State(curr_state_value)]
                new_states_b = [
                    State((q_a, state_b.value)) for state_b in epsilon_transitions_b
                ]
                state_dict[EPSILON].update(new_states_b)
                next_states_iterables.append(new_states_b)

            # Add all transitions moving over same input symbols
            for symbol in new_input_symbols:
                # Get end states considering the wildcards.
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

            # Finally, try visiting every state we found.
            for product_state in chain.from_iterable(next_states_iterables):
                if product_state not in new_states:
                    new_states.add(product_state)
                    if (
                        isinstance(product_state.value, tuple)
                        and len(product_state.value) == 2  # noqa: PLR2004
                    ):
                        queue.append(product_state.value)

        new_final_states: set[State] = set()
        possible_final_states = {
            State((q_a.value, q_b.value))
            for q_a in self.final_states
            for q_b in other.final_states
        }
        for possible_final_state in possible_final_states:
            if possible_final_state in new_states:
                new_final_states.add(possible_final_state)

        result.set_input_symbols(new_input_symbols)
        result.set_transitions(new_transitions)
        result.add_states(new_states)
        result.set_final_states(new_final_states)

        return result
