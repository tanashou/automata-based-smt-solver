# automata-lib v8.4.0 | MIT License | github.com/caleb531/automata
from collections import defaultdict, deque
from itertools import chain, product, repeat
from typing import Any

from automata_based_smt_solver.automata.input_symbol import InputSymbol, epsilon

type NFAStateT = Any
type NFATransitionT = defaultdict[NFAStateT, defaultdict[InputSymbol, set[NFAStateT]]]


class NFA:
    def __init__(
        self,
        *,
        states: set[NFAStateT],
        input_symbols: set[InputSymbol],
        transitions: NFATransitionT,
        initial_state: NFAStateT,
        final_states: set[NFAStateT],
        mask: int,
    ) -> None:
        self._states = states
        self._input_symbols = input_symbols
        self._transitions = transitions
        self._initial_state = initial_state
        self._final_states = final_states
        self._mask = mask

    def __str__(self) -> str:
        # Convert defaultdict to dict
        d = {k: dict(v) for k, v in self.transitions.items()}
        return (
            f"states={self.states},\n"
            f"input_symbols={self.input_symbols},\n"
            f"transitions={d},\n"
            f"initial_state={self.initial_state},\n"
            f"final_states={self.final_states}"
        )

    @property
    def states(self) -> set[NFAStateT]:
        return self._states

    @property
    def input_symbols(self) -> set[InputSymbol]:
        return self._input_symbols

    @property
    def transitions(self) -> NFATransitionT:
        return self._transitions

    @property
    def initial_state(self) -> NFAStateT:
        return self._initial_state

    @property
    def final_states(self) -> set[NFAStateT]:
        return self._final_states

    @property
    def mask(self) -> int:
        return self._mask

    def add_state(self, new_state: NFAStateT) -> None:
        self._states.add(new_state)

    def add_states(self, new_states: set[NFAStateT]) -> None:
        self._states.update(new_states)

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
    def _create_input_symbols_from_mask(mask: int) -> set[InputSymbol]:
        bit_length = mask.bit_length()
        bits = [(mask >> i) & 1 for i in reversed(range(bit_length))]
        options = [[0, 1] if bit == 1 else [0] for bit in bits]

        return {
            InputSymbol(
                sum(bit << (bit_length - 1 - idx) for idx, bit in enumerate(combo))
            )
            for combo in product(*options)
        }

    # 毎回新しく作りたくない。足りない部分のみを作る
    @staticmethod
    def _create_insufficient_input_symbols(xor_mask: int) -> set[InputSymbol]:
        """Create input symbols from an XOR mask.

        When mask bit is:
        - 1: Only digit 1 is needed (already has 0)
        - 0: Both 0 and 1 are needed
        """
        if xor_mask == 0:
            return set()

        bit_length = xor_mask.bit_length()
        result = set()

        # Get all possible combinations using bit manipulation
        max_combinations = 1 << bit_length
        for i in range(max_combinations):
            # Check if this combination is valid
            if all(
                ((i >> j) & 1) == 1 if (xor_mask >> j) & 1 else True
                for j in range(bit_length)
            ):
                result.add(InputSymbol(i))

        return result

    @staticmethod
    def _union_of_input_symbols(
        symbols1: set[InputSymbol],
        symbols2: set[InputSymbol],
        mask1: int,
        mask2: int,
    ) -> set[InputSymbol]:
        new_symbols = set()
        new_symbols = NFA._create_insufficient_input_symbols(mask1 ^ mask2)

        return new_symbols | symbols1 | symbols2

    def intersection(self, other: "NFA") -> "NFA":
        new_states = set()
        new_input_symbols = self._union_of_input_symbols(
            self.input_symbols, other.input_symbols, self.mask, other.mask
        )
        new_transitions: NFATransitionT = defaultdict(lambda: defaultdict(set))
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
            epsilon_transitions_a = transitions_a.get(epsilon)
            if epsilon_transitions_a is not None:
                state_dict = new_transitions.setdefault(curr_state, defaultdict(set))
                state_dict.setdefault(epsilon, set()).update(
                    zip(epsilon_transitions_a, repeat(q_b))
                )
                next_states_iterables.append(
                    list(zip(epsilon_transitions_a, repeat(q_b)))
                )

            # Get transition dict for states in other
            transitions_b = other.transitions.get(q_b, {})
            # Add epsilon transitions for second set of transitions
            epsilon_transitions_b = transitions_b.get(epsilon)
            if epsilon_transitions_b is not None:
                state_dict = new_transitions.setdefault(curr_state, defaultdict(set))
                state_dict.setdefault(epsilon, set()).update(
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
            mask=self.mask | other.mask,
        )
