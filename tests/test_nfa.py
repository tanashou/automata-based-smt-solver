from itertools import chain, product

import pytest

from automata_based_smt_solver.automata.input_symbol import EPSILON, InputSymbol
from automata_based_smt_solver.automata.nfa import NFA
from automata_based_smt_solver.automata.state import State


@pytest.fixture
def sample_nfa():
    """Create a sample NFA that accepts the regular expression (0|1)*01."""
    mask = "1"
    nfa = NFA()

    # Add states
    for state in ["q0", "q1", "q2"]:
        nfa.add_state(state)

    # Set initial and final states
    nfa.set_initial_state("q0")
    nfa.add_final_state("q2")

    nfa.add_transition("q0", InputSymbol("0", mask), "q0")
    nfa.add_transition("q0", InputSymbol("0", mask), "q1")
    nfa.add_transition("q0", InputSymbol("1", mask), "q0")

    nfa.add_transition("q1", InputSymbol("1", mask), "q2")

    return nfa


@pytest.fixture
def sample_nfa_with_epsilon():
    """Create a sample NFA that accepts the regular expression (0|1)*01 with epsilon."""
    mask = "1"
    nfa = NFA()

    # Add states
    for state in ["q0", "q1", "q2", "q3", "q4", "q5"]:
        nfa.add_state(state)

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
def sample_nfa2():
    """Create a sample NFA that accepts the regular expression 0*1*."""
    mask = "1"
    nfa = NFA()

    # Add states
    for state in ["q0", "q1", "q2"]:
        nfa.add_state(state)

    # Set initial and final states
    nfa.set_initial_state("q0")
    nfa.add_final_state("q2")

    nfa.add_transition("q0", EPSILON, "q1")
    nfa.add_transition("q1", InputSymbol("0", mask), "q1")
    nfa.add_transition("q1", EPSILON, "q2")
    nfa.add_transition("q2", InputSymbol("1", mask), "q2")

    return nfa


def test_transitions(sample_nfa):
    """Test that transitions work as expected."""
    # Get states
    q0 = State("q0", sample_nfa.id)
    q1 = State("q1", sample_nfa.id)
    q2 = State("q2", sample_nfa.id)

    # Test transitions
    assert sample_nfa.get_next_states(q0, InputSymbol("0", "1")) == {q0, q1}
    assert sample_nfa.get_next_states(q0, InputSymbol("1", "1")) == {q0}
    assert sample_nfa.get_next_states(q1, InputSymbol("1", "1")) == {q2}

    # Test non-existent transitions return empty set
    assert sample_nfa.get_next_states(q1, InputSymbol("0", "1")) == set()
    assert sample_nfa.get_next_states(q2, InputSymbol("0", "1")) == set()


def test_add_state():
    """Test adding states to an NFA."""
    nfa = NFA()
    state_names = ["q0", "q1"]

    for state_name in state_names:
        nfa.add_state(state_name)

    for state_name in state_names:
        assert State(state_name, nfa.id) in nfa.states
    assert len(nfa.states) == len(state_names)


def test_add_duplicate_state():
    """Test adding a duplicate state has no effect."""
    nfa = NFA()
    nfa.add_state("q0")
    initial_state_count = len(nfa.states)

    # Add the same state again
    nfa.add_state("q0")

    assert len(nfa.states) == initial_state_count


def test_add_transition():
    """Test adding transitions to an NFA."""
    nfa = NFA()
    nfa.add_state("q0")
    nfa.add_state("q1")

    symbol = InputSymbol("1", "1")
    nfa.add_transition("q0", symbol, "q1")

    q0 = State("q0", nfa.id)
    q1 = State("q1", nfa.id)
    assert nfa.get_next_states(q0, symbol) == {q1}


def test_accepts_sample_nfa(sample_nfa):
    """Test if the NFA accepts a string."""
    # Test strings that should be accepted (all end with '01')
    accepted_strings = [
        "01",
        "001",
        "101",
    ]

    # Test strings that should be rejected
    rejected_strings = [
        "",
        "0",
        "1",
        "10",
        "00",
        "11",
        "000",
        "010",
        "011",
        "100",
        "110",
        "111",
    ]

    # Convert strings to proper InputSymbol format
    mask = "1"
    accepted_inputs = [
        [InputSymbol(bit, mask) for bit in string] for string in accepted_strings
    ]
    rejected_inputs = [
        [InputSymbol(bit, mask) for bit in string] for string in rejected_strings
    ]

    # Test sample_nfa
    for i, input_str in enumerate(accepted_inputs):
        assert sample_nfa.accepts_input(input_str), (
            f"NFA should accept {accepted_strings[i]}"
        )

    for i, input_str in enumerate(rejected_inputs):
        assert not sample_nfa.accepts_input(input_str), (
            f"NFA should reject {rejected_strings[i]}"
        )


def test_accepts_sample_nfa_with_epsilon(sample_nfa_with_epsilon):
    accepted_strings = [
        "01",
        "001",
        "101",
    ]

    # Test strings that should be rejected
    rejected_strings = [
        "",
        "0",
        "1",
        "10",
        "00",
        "11",
        "000",
        "010",
        "011",
        "100",
        "110",
        "111",
    ]

    # Convert strings to proper InputSymbol format
    mask = "1"
    accepted_inputs = [
        [InputSymbol(bit, mask) for bit in string] for string in accepted_strings
    ]
    rejected_inputs = [
        [InputSymbol(bit, mask) for bit in string] for string in rejected_strings
    ]

    # Test sample_nfa_with_epsilon
    for i, input_str in enumerate(accepted_inputs):
        assert sample_nfa_with_epsilon.accepts_input(input_str), (
            f"NFA with epsilon should accept {accepted_strings[i]}"
        )

    for i, input_str in enumerate(rejected_inputs):
        assert not sample_nfa_with_epsilon.accepts_input(input_str), (
            f"NFA with epsilon should reject {rejected_strings[i]}"
        )


def test_accept_sample_nfa_with_wildcard(sample_nfa):
    """Test if the NFA accepts strings with wildcard characters."""
    # '01' を受理するので'**'も受理する。2文字以下は受理しない。
    mask = "0"
    accepted_strings = [
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
    ]  # '**' or '***'
    rejected_strings = [
        "",
        "0",
        "1",
    ]  # '' or '*'

    # Convert strings to proper InputSymbol format
    accepted_inputs = [
        [InputSymbol(bit, mask) for bit in string] for string in accepted_strings
    ]
    rejected_inputs = [
        [InputSymbol(bit, mask) for bit in string] for string in rejected_strings
    ]

    # Test sample_nfa
    # Test accepted strings
    for i, input_str in enumerate(accepted_inputs):
        assert sample_nfa.accepts_input(input_str), (
            f"NFA should accept {accepted_strings[i]}"
        )
    # Test rejected strings
    for i, input_str in enumerate(rejected_inputs):
        assert not sample_nfa.accepts_input(input_str), (
            f"NFA should reject {rejected_strings[i]}"
        )


def test_accepts_sample_nfa2(sample_nfa2):
    """Test if the NFA accepts a string. 0*1*."""
    accepted_strings = [
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

    # Test strings that should be rejected
    rejected_strings = [
        "10",
        "010",
        "100",
        "101",
        "110",
    ]

    # Convert strings to proper InputSymbol format
    mask = "1"
    accepted_inputs = [
        [InputSymbol(bit, mask) for bit in string] for string in accepted_strings
    ]
    rejected_inputs = [
        [InputSymbol(bit, mask) for bit in string] for string in rejected_strings
    ]

    # Test sample_nfa2
    for i, input_str in enumerate(accepted_inputs):
        assert sample_nfa2.accepts_input(input_str), (
            f"NFA should accept {accepted_strings[i]}"
        )

    for i, input_str in enumerate(rejected_inputs):
        assert not sample_nfa2.accepts_input(input_str), (
            f"NFA should reject {rejected_strings[i]}"
        )


# Helper function to create InputSymbol sets
def create_symbols(*bits: str, mask: str) -> set[InputSymbol]:
    return {InputSymbol(bit, mask) for bit in bits}


@pytest.mark.parametrize(
    ("mask", "expected_symbols"),
    [
        ("110", create_symbols("000", "010", "100", "110", mask="110")),
        (
            "",
            set(),
        ),
        (
            "1",
            create_symbols("0", "1", mask="1"),
        ),
        (
            "111",
            create_symbols(
                "000", "001", "010", "011", "100", "101", "110", "111", mask="111"
            ),
        ),
    ],
)
def test_union_of_input_symbols(mask, expected_symbols):
    new_symbols = NFA.create_input_symbols_from_mask(mask)
    assert new_symbols == expected_symbols


def test_union_operation(sample_nfa, sample_nfa2):
    """Test the union operation between two NFAs."""
    # Union should accept either '0' or '1'
    union_nfa = sample_nfa.union(sample_nfa2)

    mask = "1"

    # Keep these as lists to maintain index order for assertions
    accepted_strings_sample1 = [
        "01",
        "001",
        "101",
    ]
    accepted_strings_sample2 = [
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
    accepted_strings = list(
        set(accepted_strings_sample1) | set(accepted_strings_sample2)
    )
    accepted_inputs = [
        [InputSymbol(bit, mask) for bit in string] for string in accepted_strings
    ]

    result = list(chain(*(product("01", repeat=n) for n in range(4))))
    all_combs_upto_3_digit = {"".join(bits) for bits in result}
    rejected_strings = list(set(all_combs_upto_3_digit) - set(accepted_strings))
    rejected_inputs = [
        [InputSymbol(bit, mask) for bit in string] for string in rejected_strings
    ]

    for i, input_str in enumerate(accepted_inputs):
        assert union_nfa.accepts_input(input_str), (
            f"NFA should accept {accepted_strings[i]}"
        )
    for i, input_str in enumerate(rejected_inputs):
        assert not union_nfa.accepts_input(input_str), (
            f"NFA should reject {rejected_strings[i]}"
        )
