from collections import defaultdict

import pytest

from automata_based_smt_solver.automata.input_symbol import InputSymbol
from automata_based_smt_solver.automata.nfa import NFA


class TestNFA:
    @pytest.fixture
    def nfa(self):
        states = {"q0", "q1", "q2"}
        input_symbols = {InputSymbol(0b0), InputSymbol(0b1)}
        initial_state = "q0"
        final_states = {"q2"}
        nfa = NFA(
            states=states,
            input_symbols=input_symbols,
            transitions=defaultdict(lambda: defaultdict(set)),
            initial_state=initial_state,
            final_states=final_states,
        )
        nfa.add_transition("q0", InputSymbol(0b0), "q0")
        nfa.add_transition("q0", InputSymbol(0b1), "q1")
        nfa.add_transition("q1", InputSymbol(0b0), "q2")
        return nfa

    @pytest.fixture
    def other_nfa(self):
        states = {"q0", "q1", "q2"}
        input_symbols = {InputSymbol(0b0), InputSymbol(0b1)}
        initial_state = "q0"
        final_states = {"q2"}
        nfa = NFA(
            states=states,
            input_symbols=input_symbols,
            transitions=defaultdict(lambda: defaultdict(set)),
            initial_state=initial_state,
            final_states=final_states,
        )
        nfa.add_transition("q0", InputSymbol(0b0), "q0")
        nfa.add_transition("q0", InputSymbol(0b1), "q1")
        nfa.add_transition("q1", InputSymbol(0b0), "q2")
        return nfa

    def test_initial_state(self, nfa):
        assert nfa.initial_state == "q0"

    def test_final_states(self, nfa):
        assert nfa.final_states == {"q2"}

    @pytest.mark.parametrize(
        ("current_state", "symbol", "expected_states"),
        [
            ("q0", InputSymbol(0b0), {"q0"}),
            ("q0", InputSymbol(0b1), {"q1"}),
            ("q1", InputSymbol(0b0), {"q2"}),
        ],
    )
    def test_transitions(self, nfa, current_state, symbol, expected_states):
        assert nfa.get_next_states(current_state, symbol) == expected_states

    def test_add_state(self, nfa):
        nfa.add_state("q3")
        assert "q3" in nfa.states

    def test_add_transition(self, nfa):
        nfa.add_transition("q2", InputSymbol(0b0), "q3")
        assert nfa.get_next_states("q2", InputSymbol(0b0)) == {"q3"}

    def test_dfs_with_path(self, nfa):
        path = nfa.dfs_with_path()
        assert path == [InputSymbol(0b1), InputSymbol(0b0)]

    def test_bfs_with_path(self, nfa):
        path = nfa.bfs_with_path()
        assert path == [InputSymbol(0b1), InputSymbol(0b0)]

    def test_intersection(self, nfa, other_nfa):
        intersection = nfa.intersection(other_nfa)
        assert intersection.final_states == {"q2"}
