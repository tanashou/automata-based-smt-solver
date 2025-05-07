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
        for state in ["q0", "q1", "q2"]:
            nfa.add_state(state)

        nfa.add_input_symbol(InputSymbol("0", mask))
        nfa.add_input_symbol(InputSymbol("1", mask))

        # Set initial and final states
        nfa.set_initial_state("q0")
        nfa.add_final_state("q2")

        nfa.add_transition("q0", InputSymbol("0", mask), "q0")
        nfa.add_transition("q0", InputSymbol("0", mask), "q1")
        nfa.add_transition("q0", InputSymbol("1", mask), "q0")
        nfa.add_transition("q1", InputSymbol("1", mask), "q2")

        return nfa

    @pytest.fixture
    def nfa_ends_with_01_epsilon(self):
        """Create a NFA that accepts the regular expression (0|1)*01 with epsilon."""
        mask = "1"
        nfa = NFA()

        # Add states
        for state in ["q0", "q1", "q2", "q3", "q4", "q5"]:
            nfa.add_state(state)

        nfa.add_input_symbol(InputSymbol("0", mask))
        nfa.add_input_symbol(InputSymbol("1", mask))

        # Set initial and final states
        nfa.set_initial_state("q0")
        nfa.add_final_state("q5")

        nfa.add_transition("q0", EPSILON, "q1")
        nfa.add_transition("q1", InputSymbol("0", mask), "q1")
        nfa.add_transition("q1", InputSymbol("1", mask), "q1")
        nfa.add_transition("q1", EPSILON, "q2")
        nfa.add_transition("q2", InputSymbol("0", mask), "q3")
        nfa.add_transition("q3", InputSymbol("1", mask), "q4")
        nfa.add_transition("q4", EPSILON, "q5")

        return nfa

    @pytest.fixture
    def nfa_zero_star_one_star(self):
        """Create a NFA that accepts the regular expression 0*1*."""
        mask = "1"
        nfa = NFA()

        # Add states
        for state in ["q0", "q1", "q2"]:
            nfa.add_state(state)

        nfa.add_input_symbol(InputSymbol("0", mask))
        nfa.add_input_symbol(InputSymbol("1", mask))

        # Set initial and final states
        nfa.set_initial_state("q0")
        nfa.add_final_state("q2")

        nfa.add_transition("q0", EPSILON, "q1")
        nfa.add_transition("q1", InputSymbol("0", mask), "q1")
        nfa.add_transition("q1", EPSILON, "q2")
        nfa.add_transition("q2", InputSymbol("1", mask), "q2")

        return nfa

    def test_transitions(self, nfa_ends_with_01):
        """Test that transitions work as expected."""
        # Get states
        q0 = State("q0", nfa_ends_with_01.id)
        q1 = State("q1", nfa_ends_with_01.id)
        q2 = State("q2", nfa_ends_with_01.id)

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
        state_names = ["q0", "q1"]

        for state_name in state_names:
            nfa.add_state(state_name)

        for state_name in state_names:
            assert State(state_name, nfa.id) in nfa.states
        assert len(nfa.states) == len(state_names)

    def test_add_duplicate_state(self):
        """Test adding a duplicate state has no effect."""
        nfa = NFA()
        nfa.add_state("q0")
        initial_state_count = len(nfa.states)
        nfa.add_state("q0")  # Add the same state again
        assert len(nfa.states) == initial_state_count

    def test_add_transition(self):
        """Test adding transitions to an NFA."""
        nfa = NFA()
        nfa.add_state("q0")
        nfa.add_state("q1")

        symbol = InputSymbol("1", "1")
        nfa.add_transition("q0", symbol, "q1")

        q0 = State("q0", nfa.id)
        q1 = State("q1", nfa.id)
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

    def test_union_operation(self, nfa_ends_with_01, nfa_zero_star_one_star):
        """Test the union operation between two NFAs."""
        union_nfa = nfa_ends_with_01.union(nfa_zero_star_one_star)
        mask = "1"

        accepted_strings = list(
            set(self.STRINGS_ACCEPTED_BY_ENDS_WITH_01)
            | set(self.STRINGS_ACCEPTED_BY_ZERO_STAR_ONE_STAR)
        )
        rejected_strings = list(self.ALL_STRINGS_UP_TO_LENGTH_3 - set(accepted_strings))

        TestNFA.assert_nfa_accepts_rejects(
            union_nfa, accepted_strings, rejected_strings, mask
        )

    def test_union_operation_with_epsilon(
        self, nfa_ends_with_01_epsilon, nfa_zero_star_one_star
    ):
        """Test the union operation between an NFA with epsilon ."""
        union_nfa = nfa_ends_with_01_epsilon.union(nfa_zero_star_one_star)
        mask = "1"

        accepted_strings = list(
            set(self.STRINGS_ACCEPTED_BY_ENDS_WITH_01)
            | set(self.STRINGS_ACCEPTED_BY_ZERO_STAR_ONE_STAR)
        )
        rejected_strings = list(self.ALL_STRINGS_UP_TO_LENGTH_3 - set(accepted_strings))

        TestNFA.assert_nfa_accepts_rejects(
            union_nfa,
            accepted_strings,
            rejected_strings,
            mask,
            "Union NFA with epsilon",
        )

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
