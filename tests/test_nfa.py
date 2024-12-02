from collections import defaultdict

import pytest

from automata_based_smt_solver.automata.input_symbol import InputSymbol
from automata_based_smt_solver.automata.nfa import NFA


@pytest.fixture
def nfa():
    mask = 0b1
    states = {"q0", "q1", "q2"}
    input_symbols = NFA._create_input_symbols_from_mask(mask)
    initial_state = "q0"
    final_states = {"q2"}
    nfa = NFA(
        states=states,
        input_symbols=input_symbols,
        transitions=defaultdict(lambda: defaultdict(set)),
        initial_state=initial_state,
        final_states=final_states,
        mask=mask,
    )
    nfa.add_transition("q0", InputSymbol(0b0), "q0")
    nfa.add_transition("q0", InputSymbol(0b1), "q1")
    nfa.add_transition("q1", InputSymbol(0b0), "q2")
    return nfa


@pytest.fixture
def other_nfa():
    mask = 0b1
    states = {"q0", "q1", "q2"}
    input_symbols = NFA._create_input_symbols_from_mask(mask)
    initial_state = "q0"
    final_states = {"q2"}
    nfa = NFA(
        states=states,
        input_symbols=input_symbols,
        transitions=defaultdict(lambda: defaultdict(set)),
        initial_state=initial_state,
        final_states=final_states,
        mask=mask,
    )
    nfa.add_transition("q0", InputSymbol(0b0), "q0")
    nfa.add_transition("q0", InputSymbol(0b1), "q1")
    nfa.add_transition("q1", InputSymbol(0b0), "q2")
    return nfa


def test_initial_state(nfa):
    assert nfa.initial_state == "q0"


def test_final_states(nfa):
    assert nfa.final_states == {"q2"}


@pytest.mark.parametrize(
    ("current_state", "symbol", "expected_states"),
    [
        ("q0", InputSymbol(0b0), {"q0"}),
        ("q0", InputSymbol(0b1), {"q1"}),
        ("q1", InputSymbol(0b0), {"q2"}),
    ],
)
def test_transitions(nfa, current_state, symbol, expected_states):
    assert nfa.get_next_states(current_state, symbol) == expected_states


def test_add_state(nfa):
    nfa.add_state("q3")
    assert "q3" in nfa.states


def test_add_transition(nfa):
    nfa.add_transition("q2", InputSymbol(0b0), "q3")
    assert nfa.get_next_states("q2", InputSymbol(0b0)) == {"q3"}


def test_dfs_with_path(nfa):
    path = nfa.dfs_with_path()
    assert path == [InputSymbol(0b1), InputSymbol(0b0)]


def test_bfs_with_path(nfa):
    path = nfa.bfs_with_path()
    assert path == [InputSymbol(0b1), InputSymbol(0b0)]


# Helper function to create InputSymbol sets
def create_symbols(*bits: int) -> set[InputSymbol]:
    return {InputSymbol(bit) for bit in bits}


def create_symbols_from_mask(mask: int) -> set[InputSymbol]:
    return {InputSymbol(1 << i) for i in range(32) if mask & (1 << i)}


@pytest.mark.parametrize(
    ("symbols1", "symbols2", "mask1", "mask2", "expected_symbols"),
    [
        (
            NFA._create_input_symbols_from_mask(0b110),
            NFA._create_input_symbols_from_mask(0b011),
            0b110,
            0b011,
            NFA._create_input_symbols_from_mask(0b110 | 0b011),
        ),
        (
            NFA._create_input_symbols_from_mask(0b001),
            NFA._create_input_symbols_from_mask(0b011),
            0b001,
            0b011,
            NFA._create_input_symbols_from_mask(0b001 | 0b011),
        ),
    ],
)
def test_union_of_input_symbols(symbols1, symbols2, mask1, mask2, expected_symbols):
    new_symbols = NFA._union_of_input_symbols(symbols1, symbols2, mask1, mask2)
    assert new_symbols == expected_symbols
