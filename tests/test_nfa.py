import pytest
from smt_solver.automata.input_symbol import InputSymbol
from smt_solver.automata.nfa import NFA
from smt_solver.automata.state import State


@pytest.fixture
def nfa():
    mask = "1"
    nfa = NFA()
    nfa.add_state("q0")
    nfa.add_state("q1")
    nfa.add_state("q2")

    nfa.add_transition("q0", InputSymbol("0", mask), "q0")
    nfa.add_transition("q0", InputSymbol("1", mask), "q1")
    nfa.add_transition("q1", InputSymbol("0", mask), "q2")

    nfa.add_final_state("q2")

    return nfa


@pytest.mark.parametrize(
    ("current_state_value", "symbol", "expected_state_values"),
    [
        ("q0", InputSymbol("0", "1"), {"q0"}),
        ("q0", InputSymbol("1", "1"), {"q1"}),
        ("q1", InputSymbol("0", "1"), {"q2"}),
    ],
)
def test_transitions(nfa, current_state_value, symbol, expected_state_values):
    current_state = State(current_state_value, nfa.id)
    expected_states = {State(val, nfa.id) for val in expected_state_values}
    next_states = nfa.get_next_states(current_state, symbol)
    assert next_states == expected_states


def test_add_state(nfa):
    nfa.add_state("q3")
    assert State("q3", nfa.id) in nfa.states


def test_add_transition(nfa):
    nfa.add_transition("q2", InputSymbol("0", "1"), "q3")
    assert nfa.get_next_states(State("q2", nfa.id), InputSymbol("0", "1")) == {
        State("q3", nfa.id)
    }


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
