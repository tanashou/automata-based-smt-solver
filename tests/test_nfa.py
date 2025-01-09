from collections import defaultdict

import pytest

from automata_based_smt_solver.automata.input_symbol import InputSymbol
from automata_based_smt_solver.automata.nfa import NFA
from automata_based_smt_solver.automata.state import State


@pytest.fixture
def nfa():
    mask = "1"
    q0, q1, q2 = State("q0"), State("q1"), State("q2")
    states = {q0, q1, q2}
    input_symbols = NFA.create_input_symbols_from_mask(mask)
    initial_state = q0
    final_states = {q2}
    nfa = NFA(
        states=states,
        input_symbols=input_symbols,
        transitions=defaultdict(lambda: defaultdict(set)),
        initial_state=initial_state,
        final_states=final_states,
    )
    nfa.add_transition(q0, InputSymbol("0", mask), q0)
    nfa.add_transition(q0, InputSymbol("1", mask), q1)
    nfa.add_transition(q1, InputSymbol("0", mask), q2)
    return nfa


@pytest.mark.parametrize(
    ("current_state", "symbol", "expected_states"),
    [
        (State("q0"), InputSymbol("0", "1"), {State("q0")}),
        (State("q0"), InputSymbol("1", "1"), {State("q1")}),
        (State("q1"), InputSymbol("0", "1"), {State("q2")}),
    ],
)
def test_transitions(nfa, current_state, symbol, expected_states):
    assert nfa.get_next_states(current_state, symbol) == expected_states


def test_add_state(nfa):
    nfa.add_state(State("q3"))
    assert State("q3") in nfa.states


def test_add_transition(nfa):
    nfa.add_transition(State("q2"), InputSymbol("0", "1"), State("q3"))
    assert nfa.get_next_states(State("q2"), InputSymbol("0", "1")) == {State("q3")}


def test_dfs_with_path(nfa):
    path = nfa.dfs_with_path()
    assert path == [InputSymbol("1", "1"), InputSymbol("0", "1")]


def test_bfs_with_path(nfa):
    path = nfa.bfs_with_path()
    assert path == [InputSymbol("1", "1"), InputSymbol("0", "1")]


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
