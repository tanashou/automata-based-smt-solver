from itertools import chain, product
from typing import ClassVar

import pytest

from automata_based_smt_solver.automata.input_symbol import EPSILON, InputSymbol
from automata_based_smt_solver.automata.nfa import NFA
from automata_based_smt_solver.automata.state import State


def create_symbols(*bits: str, mask: str) -> set[InputSymbol]:
    return {InputSymbol(bit, mask) for bit in bits}


class TestNFA:
    # Common test data as class constants
    STRINGS_ACCEPTED_BY_ENDS_WITH_01: ClassVar[list[str]] = [
        "01",
        "001",
        "101",
    ]
    STRINGS_ACCEPTED_BY_ZERO_STAR_ONE_STAR: ClassVar[list[str]] = [
        "",
        "0",
        "1",
        "00",
        "01",
        "11",
        "000",
        "001",
        "011",
        "111",
    ]

    @classmethod
    def setup_class(cls) -> None:
        """Set up common test data."""
        cls.ALL_STRINGS_UP_TO_LENGTH_3 = set(cls.get_all_strings_up_to_length("01", 3))

        # Compute common rejected strings
        cls.STRINGS_REJECTED_BY_ENDS_WITH_01 = list(
            cls.ALL_STRINGS_UP_TO_LENGTH_3 - set(cls.STRINGS_ACCEPTED_BY_ENDS_WITH_01)
        )
        cls.STRINGS_REJECTED_BY_ZERO_STAR_ONE_STAR = list(
            cls.ALL_STRINGS_UP_TO_LENGTH_3
            - set(cls.STRINGS_ACCEPTED_BY_ZERO_STAR_ONE_STAR)
        )

        # Common wildcard acceptances
        cls.STRINGS_ACCEPTED_WITH_WILDCARD = [
            "00",
            "01",
            "10",
            "11",
            "000",
            "001",
            "010",
            "011",
            "100",
            "101",
            "110",
            "111",
        ]
        cls.STRINGS_REJECTED_WITH_WILDCARD = [
            "",
            "0",
            "1",
        ]

    @staticmethod
    def convert_strings_to_inputs(strings, mask) -> list[list[InputSymbol]]:
        """Convert string lists to InputSymbol format."""
        return [[InputSymbol(bit, mask) for bit in string] for string in strings]

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
    def nfa_ends_with_01(self):
        """Create a NFA that accepts the regular expression (0|1)*01."""
        mask = "1"
        nfa = NFA()

        # Add states
        for state in ["q1", "q2"]:
            nfa.add_state(State(state))

        nfa.add_input_symbol(InputSymbol("0", mask))
        nfa.add_input_symbol(InputSymbol("1", mask))

        nfa.add_final_state(State("q2"))

        nfa.add_transition(nfa.initial_state, InputSymbol("0", mask), nfa.initial_state)
        nfa.add_transition(nfa.initial_state, InputSymbol("0", mask), State("q1"))
        nfa.add_transition(nfa.initial_state, InputSymbol("1", mask), nfa.initial_state)
        nfa.add_transition(State("q1"), InputSymbol("1", mask), State("q2"))

        return nfa

    @pytest.fixture
    def nfa_ends_with_01_or_00(self):
        """Create a NFA that accepts the regular expression (0|1)*01."""
        mask = "1"
        nfa = NFA()

        # Add states
        for state in ["q1", "q2"]:
            nfa.add_state(State(state))

        nfa.add_input_symbol(InputSymbol("0", mask))
        nfa.add_input_symbol(InputSymbol("1", mask))

        nfa.add_final_state(State("q2"))

        nfa.add_transition(nfa.initial_state, InputSymbol("0", mask), nfa.initial_state)
        nfa.add_transition(nfa.initial_state, InputSymbol("0", mask), State("q1"))
        nfa.add_transition(nfa.initial_state, InputSymbol("1", mask), nfa.initial_state)
        nfa.add_transition(State("q1"), InputSymbol("1", mask), State("q2"))
        nfa.add_transition(State("q1"), InputSymbol("0", mask), State("q2"))  # 追加分

        return nfa

    @pytest.fixture
    def nfa_ends_with_01_epsilon(self):
        """Create a NFA that accepts the regular expression (0|1)*01 with epsilon."""
        mask = "1"
        nfa = NFA()

        # Add states
        for state in [nfa.initial_state, "q1", "q2", "q3", "q4", "q5"]:
            if isinstance(state, str):
                nfa.add_state(State(state))
            else:
                nfa.add_state(state)

        nfa.add_input_symbol(InputSymbol("0", mask))
        nfa.add_input_symbol(InputSymbol("1", mask))

        nfa.add_final_state(State("q5"))

        nfa.add_transition(nfa.initial_state, EPSILON, State("q1"))
        nfa.add_transition(State("q1"), InputSymbol("0", mask), State("q1"))
        nfa.add_transition(State("q1"), InputSymbol("1", mask), State("q1"))
        nfa.add_transition(State("q1"), EPSILON, State("q2"))
        nfa.add_transition(State("q2"), InputSymbol("0", mask), State("q3"))
        nfa.add_transition(State("q3"), InputSymbol("1", mask), State("q4"))
        nfa.add_transition(State("q4"), EPSILON, State("q5"))

        return nfa

    @pytest.fixture
    def nfa_starts_with_01(self):
        """Create a NFA that accepts the regular expression 01(0|1)*."""
        mask = "1"
        nfa = NFA()

        # Add states
        for state in ["q1", "q2"]:
            nfa.add_state(State(state))

        nfa.add_input_symbol(InputSymbol("0", mask))
        nfa.add_input_symbol(InputSymbol("1", mask))

        nfa.add_final_state(State("q2"))

        nfa.add_transition(nfa.initial_state, InputSymbol("0", mask), State("q1"))
        nfa.add_transition(State("q1"), InputSymbol("1", mask), State("q2"))
        nfa.add_transition(State("q2"), InputSymbol("0", mask), State("q2"))
        nfa.add_transition(State("q2"), InputSymbol("1", mask), State("q2"))

        return nfa

    @pytest.fixture
    def nfa_zero_star_one_star(self):
        """Create a NFA that accepts the regular expression 0*1*."""
        mask = "1"
        nfa = NFA()

        # Add states
        for state in [nfa.initial_state, "q1", "q2"]:
            if isinstance(state, str):
                nfa.add_state(State(state))
            else:
                nfa.add_state(state)

        nfa.add_input_symbol(InputSymbol("0", mask))
        nfa.add_input_symbol(InputSymbol("1", mask))

        # Set initial and final states
        nfa.add_final_state(State("q2"))

        nfa.add_transition(nfa.initial_state, EPSILON, State("q1"))
        nfa.add_transition(State("q1"), InputSymbol("0", mask), State("q1"))
        nfa.add_transition(State("q1"), EPSILON, State("q2"))
        nfa.add_transition(State("q2"), InputSymbol("1", mask), State("q2"))

        return nfa

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
        q1 = State("q1")
        q2 = State("q2")

        # Test transitions
        assert nfa_ends_with_01.get_next_states(q0, InputSymbol("0", "1")) == {q0, q1}
        assert nfa_ends_with_01.get_next_states(q0, InputSymbol("1", "1")) == {q0}
        assert nfa_ends_with_01.get_next_states(q1, InputSymbol("1", "1")) == {q2}

        # Test non-existent transitions return empty set
        assert nfa_ends_with_01.get_next_states(q1, InputSymbol("0", "1")) == set()
        assert nfa_ends_with_01.get_next_states(q2, InputSymbol("0", "1")) == set()

    def test_add_state(self):
        """Test adding states to an NFA."""
        nfa = NFA()
        state_objs = [nfa.initial_state, State("q1")]

        for state_obj in state_objs:
            nfa.add_state(state_obj)

        for state_obj in state_objs:
            assert state_obj in nfa.states
        assert len(nfa.states) == len(state_objs)

    def test_add_duplicate_state(self):
        """Test adding a duplicate state has no effect."""
        nfa = NFA()
        nfa.add_state(nfa.initial_state)
        initial_state_count = len(nfa.states)
        nfa.add_state(nfa.initial_state)  # Add the same state again
        assert len(nfa.states) == initial_state_count

    def test_add_transition(self):
        """Test adding transitions to an NFA."""
        nfa = NFA()
        nfa.add_state(nfa.initial_state)
        nfa.add_state(State("q1"))

        symbol = InputSymbol("1", "1")
        nfa.add_transition(nfa.initial_state, symbol, State("q1"))

        q0 = nfa.initial_state
        q1 = State("q1")
        assert nfa.get_next_states(q0, symbol) == {q1}

    def test_accepts_nfa_ends_with_01(self, nfa_ends_with_01):
        """Test if the NFA accepts a string."""
        mask = "1"
        TestNFA.assert_nfa_accepts_rejects(
            nfa_ends_with_01,
            self.STRINGS_ACCEPTED_BY_ENDS_WITH_01,
            self.STRINGS_REJECTED_BY_ENDS_WITH_01,
            mask,
        )

    def test_accepts_nfa_ends_with_01_epsilon(self, nfa_ends_with_01_epsilon):
        """Test if the NFA with epsilon accepts a string."""
        mask = "1"
        TestNFA.assert_nfa_accepts_rejects(
            nfa_ends_with_01_epsilon,
            self.STRINGS_ACCEPTED_BY_ENDS_WITH_01,
            self.STRINGS_REJECTED_BY_ENDS_WITH_01,
            mask,
            "NFA with epsilon",
        )

    def test_accept_nfa_ends_with_01_with_wildcard(self, nfa_ends_with_01):
        """Test if the NFA accepts strings with wildcard characters."""
        mask = "0"
        TestNFA.assert_nfa_accepts_rejects(
            nfa_ends_with_01,
            self.STRINGS_ACCEPTED_WITH_WILDCARD,
            self.STRINGS_REJECTED_WITH_WILDCARD,
            mask,
        )

    def test_accepts_nfa_zero_star_one_star(self, nfa_zero_star_one_star):
        """Test if the NFA accepts a string. 0*1*."""
        mask = "1"
        TestNFA.assert_nfa_accepts_rejects(
            nfa_zero_star_one_star,
            self.STRINGS_ACCEPTED_BY_ZERO_STAR_ONE_STAR,
            self.STRINGS_REJECTED_BY_ZERO_STAR_ONE_STAR,
            mask,
        )

    @pytest.mark.parametrize(
        ("mask", "expected_symbols"),
        [
            ("110", create_symbols("000", "010", "100", "110", mask="110")),
            ("", set()),
            ("1", create_symbols("0", "1", mask="1")),
            (
                "111",
                create_symbols(
                    "000", "001", "010", "011", "100", "101", "110", "111", mask="111"
                ),
            ),
        ],
    )
    def test_union_of_input_symbols(self, mask, expected_symbols):
        new_symbols = NFA.create_input_symbols_from_mask(mask)
        assert new_symbols == expected_symbols

    def test_intersection_operation(self, nfa_ends_with_01, nfa_zero_star_one_star):
        """Test the intersection operation between two NFAs."""
        intersection_nfa = nfa_ends_with_01.intersection(nfa_zero_star_one_star)
        mask = "1"

        accepted_strings = list(
            set(self.STRINGS_ACCEPTED_BY_ENDS_WITH_01)
            & set(self.STRINGS_ACCEPTED_BY_ZERO_STAR_ONE_STAR)
        )
        rejected_strings = list(self.ALL_STRINGS_UP_TO_LENGTH_3 - set(accepted_strings))

        TestNFA.assert_nfa_accepts_rejects(
            intersection_nfa, accepted_strings, rejected_strings, mask
        )

    def test_intersection_operation_with_epsilon(
        self, nfa_ends_with_01_epsilon, nfa_zero_star_one_star
    ):
        """Test the intersection operation between an NFA with epsilon ."""
        intersection_nfa = nfa_ends_with_01_epsilon.intersection(nfa_zero_star_one_star)
        mask = "1"

        # Only '01' and '001'
        accepted_strings = list(
            set(self.STRINGS_ACCEPTED_BY_ENDS_WITH_01)
            & set(self.STRINGS_ACCEPTED_BY_ZERO_STAR_ONE_STAR)
        )
        rejected_strings = list(self.ALL_STRINGS_UP_TO_LENGTH_3 - set(accepted_strings))

        TestNFA.assert_nfa_accepts_rejects(
            intersection_nfa,
            accepted_strings,
            rejected_strings,
            mask,
            "Intersection NFA with epsilon",
        )

    def test_is_acceptable(self):
        """Test the is_acceptable function for various NFA configurations."""
        # Accepting NFA: initial state is also final
        nfa1 = NFA()
        nfa1.add_final_state(nfa1.initial_state)
        assert nfa1.is_acceptable() is True

        # Non-accepting NFA: no final state
        nfa2 = NFA()
        assert nfa2.is_acceptable() is False

        # Accepting NFA: path to final state
        nfa3 = NFA()
        nfa3.add_state(State("q1"))
        nfa3.add_final_state(State("q1"))
        symbol = InputSymbol("1", "1")
        nfa3.add_input_symbol(symbol)
        nfa3.add_transition(nfa3.initial_state, symbol, State("q1"))
        assert nfa3.is_acceptable() is True

        # Non-accepting NFA: no path to final state
        nfa4 = NFA()
        nfa4.add_state(State("q1"))
        nfa4.add_final_state(State("q1"))
        # No transition from q0 to q1
        assert nfa4.is_acceptable() is False

        # Accepting NFA: epsilon transition to final state
        nfa5 = NFA()
        nfa5.add_state(State("q1"))
        nfa5.add_final_state(State("q1"))
        nfa5.add_transition(nfa5.initial_state, EPSILON, State("q1"))
        assert nfa5.is_acceptable() is True

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

        delta_1_changes = {State("q1"): {InputSymbol("0", "1"): {State("q2")}}}
        delta_2_changes = {}
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
