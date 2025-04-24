import pytest

from automata_based_smt_solver.automata.input_symbol import InputSymbol
from automata_based_smt_solver.automata.nfa import NFA
from automata_based_smt_solver.automata.state import State


@pytest.fixture
def simple_nfa():
    """Create a simple NFA that accepts strings ending with '01'."""
    mask = "1"
    nfa = NFA()
    nfa.add_state("q0")
    nfa.add_state("q1")
    nfa.add_state("q2")

    nfa.set_initial_state("q0")
    nfa.add_transition("q0", InputSymbol("0", mask), "q0")
    nfa.add_transition("q0", InputSymbol("1", mask), "q0")
    nfa.add_transition("q0", InputSymbol("0", mask), "q1")
    nfa.add_transition("q1", InputSymbol("1", mask), "q2")

    nfa.add_final_state("q2")

    return nfa


@pytest.fixture
def pattern_0_nfa():
    """Create an NFA that accepts strings with pattern '0'."""
    mask = "1"
    nfa = NFA()
    nfa.set_initial_state("s0")
    nfa.add_state("s0")
    nfa.add_state("s1")
    nfa.add_transition("s0", InputSymbol("0", mask), "s1")
    nfa.add_final_state("s1")
    return nfa


@pytest.fixture
def pattern_1_nfa():
    """Create an NFA that accepts strings with pattern '1'."""
    mask = "1"
    nfa = NFA()
    nfa.set_initial_state("t0")
    nfa.add_state("t0")
    nfa.add_state("t1")
    nfa.add_transition("t0", InputSymbol("1", mask), "t1")
    nfa.add_final_state("t1")
    return nfa


def test_transitions(simple_nfa):
    """Test that transitions work as expected."""
    # Get states
    q0 = State("q0", simple_nfa.id)
    q1 = State("q1", simple_nfa.id)
    q2 = State("q2", simple_nfa.id)

    # Test transitions
    assert simple_nfa.get_next_states(q0, InputSymbol("0", "1")) == {q0, q1}
    assert simple_nfa.get_next_states(q0, InputSymbol("1", "1")) == {q0}
    assert simple_nfa.get_next_states(q1, InputSymbol("1", "1")) == {q2}

    # Test non-existent transitions return empty set
    assert simple_nfa.get_next_states(q1, InputSymbol("0", "1")) == set()
    assert simple_nfa.get_next_states(q2, InputSymbol("0", "1")) == set()


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


def test_union_operation(pattern_0_nfa, pattern_1_nfa):
    """Test the union operation between two NFAs."""
    # Union should accept either '0' or '1'
    union_nfa = pattern_0_nfa.union(pattern_1_nfa)

    # Check that input symbols are combined
    assert union_nfa.input_symbols == pattern_0_nfa.input_symbols.union(
        pattern_1_nfa.input_symbols
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
