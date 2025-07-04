from itertools import chain, product

import pytest
from pysmt.shortcuts import Symbol
from pysmt.typing import INT

from absmt.automata.msbf_alphabet import MSBFAlphabet
from absmt.automata.msbf_alphabet_symbol import (
    MSBFAlphabetSymbol,
)
from absmt.automata.nfa import NFA, NFAStateT, NFATransitionsT


def create_symbols(*bits: str, mask: str) -> list[MSBFAlphabetSymbol]:
    return [MSBFAlphabetSymbol(bit, mask) for bit in bits]


class TestNFA:
    @staticmethod
    def convert_strings_to_inputs(strings, mask) -> list[list[MSBFAlphabetSymbol]]:
        """Convert string lists to MSBFAlphabetSymbol format."""
        return [[MSBFAlphabetSymbol(bit, mask) for bit in string] for string in strings]

    @staticmethod
    def assert_nfa_accepts_rejects(
        nfa, accepted_strings, rejected_strings, mask, nfa_name="NFA"
    ) -> None:
        """Test that NFA accepts and rejects the appropriate strings."""
        accepted_inputs = TestNFA.convert_strings_to_inputs(accepted_strings, mask)
        rejected_inputs = TestNFA.convert_strings_to_inputs(rejected_strings, mask)

        for i, input_str in enumerate(accepted_inputs):
            assert nfa.accepts_input(input_str), (
                f"{nfa_name} should accept {accepted_strings[i]}"
            )

        for i, input_str in enumerate(rejected_inputs):
            assert not nfa.accepts_input(input_str), (
                f"{nfa_name} should reject {rejected_strings[i]}"
            )

    @staticmethod
    def get_all_strings_up_to_length(alphabet, max_length) -> list[str]:
        """Generate all strings up to max_length from the given alphabet."""
        combinations = chain.from_iterable(
            product(alphabet, repeat=length) for length in range(max_length + 1)
        )
        return ["".join(combo) for combo in combinations]

    @pytest.fixture
    def msbf_alphabet_01(self):
        """Create a MSBFAlphabet with binary symbols."""
        var = Symbol("var", INT)
        return MSBFAlphabet(
            all_vars=[var],
            used_vars=[var],
        )

    @pytest.fixture
    def nfa_ends_with_01(self, msbf_alphabet_01):
        """Create a NFA that accepts the regular expression (0|1)*01."""
        # Define states
        q0 = "q0"
        q1 = "q1"
        q2 = "q2"
        states: set[NFAStateT] = {q0, q1, q2}
        # Define transitions
        symbol_0, symbol_1 = create_symbols("0", "1", mask="1")
        transitions: NFATransitionsT = {
            q0: {
                symbol_0: {q0, q1},
                symbol_1: {q0},
            },
            q1: {
                symbol_1: {q2},
            },
            q2: {},
        }
        # Define initial and final states
        initial_state = q0
        final_states: set[NFAStateT] = {q2}
        # Create NFA
        return NFA(
            states=states,
            alphabet=msbf_alphabet_01,
            transitions=transitions,
            initial_state=initial_state,
            final_states=final_states,
        )

    @pytest.fixture
    def nfa_ends_with_01_or_00(self, msbf_alphabet_01):
        """Create a NFA that accepts the regular expression (0|1)*01 or (0|1)*00."""
        # Define states
        q0 = "q0"
        q1 = "q1"
        q2 = "q2"
        states: set[NFAStateT] = {q0, q1, q2}
        # Define transitions
        symbol_0, symbol_1 = create_symbols("0", "1", mask="1")
        transitions: NFATransitionsT = {
            q0: {
                symbol_0: {q0, q1},
                symbol_1: {q0},
            },
            q1: {
                symbol_1: {q2},
                symbol_0: {q2},
            },
            q2: {},
        }
        # Define initial and final states
        initial_state = q0
        final_states: set[NFAStateT] = {q2}
        # Create NFA
        return NFA(
            states=states,
            alphabet=msbf_alphabet_01,
            transitions=transitions,
            initial_state=initial_state,
            final_states=final_states,
        )

    @pytest.fixture
    def nfa_starts_with_01(self, msbf_alphabet_01):
        """Create a NFA that accepts the regular expression 01(0|1)*."""
        # Define states
        q0 = "q0"
        q1 = "q1"
        q2 = "q2"
        states: set[NFAStateT] = {q0, q1, q2}
        # Define transitions
        symbol_0, symbol_1 = create_symbols("0", "1", mask="1")
        transitions: NFATransitionsT = {
            q0: {
                symbol_0: {q1},
            },
            q1: {
                symbol_1: {q2},
            },
            q2: {
                symbol_0: {q2},
                symbol_1: {q2},
            },
        }
        # Define initial and final states
        initial_state = q0
        final_states: set[NFAStateT] = {q2}
        # Create NFA
        return NFA(
            states=states,
            alphabet=msbf_alphabet_01,
            transitions=transitions,
            initial_state=initial_state,
            final_states=final_states,
        )

    @pytest.fixture
    def str_starts_with_01(self) -> set[str]:
        """Create a set of strings that start with '01' up to 5 digits."""
        alphabet = "01"
        max_length = 5
        result = set()
        for length in range(2, max_length + 1):
            for tail in product(alphabet, repeat=length - 2):
                s = "01" + "".join(tail)
                result.add(s)
        return result

    @pytest.fixture
    def str_ends_with_01(self) -> set[str]:
        """Create a set of strings that end with '01' up to 5 digits."""
        alphabet = "01"
        max_length = 5
        result = set()
        for length in range(2, max_length + 1):
            for head in product(alphabet, repeat=length - 2):
                s = "".join(head) + "01"
                result.add(s)
        return result

    @pytest.fixture
    def str_ends_with_01_or_00(self) -> set[str]:
        """Create a set of strings that end with '01' or '00' up to 5 digits."""
        alphabet = "01"
        max_length = 5
        result = set()
        for length in range(2, max_length + 1):
            for head in product(alphabet, repeat=length - 2):
                for suffix in ("01", "00"):
                    s = "".join(head) + suffix
                    result.add(s)
        return result

    @pytest.fixture
    def str_all_binary_up_to_5(self) -> set[str]:
        """Return all binary strings with length up to 5 (empty string included)."""
        alphabet = "01"
        max_length = 5
        result = set()
        for length in range(max_length + 1):
            for s in product(alphabet, repeat=length):
                result.add("".join(s))
        return result

    def test_transitions(self, nfa_ends_with_01):
        """Test that transitions work as expected."""
        # Get states
        q0 = nfa_ends_with_01.initial_state
        q1 = "q1"
        q2 = "q2"

        # Test transitions
        assert nfa_ends_with_01.get_next_states(q0, MSBFAlphabetSymbol("0", "1")) == {
            q0,
            q1,
        }
        assert nfa_ends_with_01.get_next_states(q0, MSBFAlphabetSymbol("1", "1")) == {
            q0
        }
        assert nfa_ends_with_01.get_next_states(q1, MSBFAlphabetSymbol("1", "1")) == {
            q2
        }

        # Test non-existent transitions return empty set
        assert (
            nfa_ends_with_01.get_next_states(q1, MSBFAlphabetSymbol("0", "1")) == set()
        )
        assert (
            nfa_ends_with_01.get_next_states(q2, MSBFAlphabetSymbol("0", "1")) == set()
        )

    def test_accepts_nfa_ends_with_01(
        self, nfa_ends_with_01, str_ends_with_01, str_all_binary_up_to_5
    ):
        """Test if the NFA accepts a string."""
        mask = "1"
        accepted_strings = list(str_ends_with_01)
        rejected_strings = list(str_all_binary_up_to_5 - str_ends_with_01)
        TestNFA.assert_nfa_accepts_rejects(
            nfa_ends_with_01,
            accepted_strings,
            rejected_strings,
            mask,
        )

    def test_intersection_operation(
        self,
        nfa_ends_with_01,
        nfa_starts_with_01,
        str_ends_with_01,
        str_starts_with_01,
        str_all_binary_up_to_5,
    ):
        """Test the intersection operation between two NFAs."""
        intersection_nfa = nfa_ends_with_01.intersection(nfa_starts_with_01)

        accepted_strings = list(str_ends_with_01 & str_starts_with_01)
        rejected_strings = list(set(str_all_binary_up_to_5) - set(accepted_strings))
        TestNFA.assert_nfa_accepts_rejects(
            intersection_nfa, accepted_strings, rejected_strings, mask="1"
        )

    def test_is_acceptable(
        self, nfa_ends_with_01, nfa_ends_with_01_or_00, nfa_starts_with_01
    ):
        # Accepting NFA: nfa_ends_with_01 has a path to a final state
        assert nfa_ends_with_01.is_acceptable() is True
        # Accepting NFA: nfa_ends_with_01_or_00 has a path to a final state
        assert nfa_ends_with_01_or_00.is_acceptable() is True
        # Accepting NFA: nfa_starts_with_01 has a path to a final state
        assert nfa_starts_with_01.is_acceptable() is True
        # Non-accepting NFA: create one with no final states
        q0 = "q0"  # Initial state
        msbf_alphabet = nfa_ends_with_01.alphabet
        transitions: NFATransitionsT = {q0: {}}
        nfa_no_final = NFA(
            states={q0},
            alphabet=msbf_alphabet,
            transitions=transitions,
            initial_state=q0,
            final_states=set(),
        )
        assert nfa_no_final.is_acceptable() is False

    def test_incremental_intersection_specific_example(
        self,
        nfa_ends_with_01,
        nfa_ends_with_01_or_00,
        nfa_starts_with_01,
        str_starts_with_01,
        str_ends_with_01_or_00,
        str_all_binary_up_to_5,
    ):
        intersected_nfa_old = nfa_ends_with_01.intersection(nfa_starts_with_01)

        delta_1_changes: NFATransitionsT = {
            "q1": {MSBFAlphabetSymbol("0", "1"): {"q2"}}
        }
        delta_2_changes: NFATransitionsT = {}
        intersected_nfa_new = NFA.incremental_intersection(
            intersected_nfa_old,
            nfa_ends_with_01_or_00,
            nfa_starts_with_01,
            delta_1_changes,
            delta_2_changes,
        )

        accepted_strings = list(str_ends_with_01_or_00 & str_starts_with_01)
        rejected_strings = list(str_all_binary_up_to_5 - set(accepted_strings))

        TestNFA.assert_nfa_accepts_rejects(
            intersected_nfa_new, accepted_strings, rejected_strings, "1"
        )
