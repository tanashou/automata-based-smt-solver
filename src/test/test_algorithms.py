import pytest
from src.my_automata.automata_algorithms import nfa_intersection, AutomataBuilder
from src.my_automata.mutable_nfa import MutableNFA as NFA, NFATransitionT
from collections import defaultdict


# Define a fixture for creating NFAs with common structure
@pytest.fixture
def sample_NFAs():
    coefs = [1, 1]
    bld1 = AutomataBuilder(coefs, 2, "equal", create_all=True)
    bld1.next()
    nfa2 = NFA(
        states={"s", "f"},
        input_symbols={"*0", "*1"},
        transitions=defaultdict(lambda: defaultdict(set)),
        initial_state="s",
        final_states={"f"},
    )
    nfa2.add_transition("s", "*0", "f")
    nfa2.add_transition("f", "*1", "f")
    nfa2.add_transition("f", "*0", "f")
    return bld1.nfa, nfa2


def test_nfa_intersection(sample_NFAs):
    """
    x + z = 2 and x >= 0
    """
    n1, n2 = sample_NFAs

    result_nfa = nfa_intersection(n1, n2)

    assert result_nfa.states == {("q0", "s"), ("-1", "f"), ("0", "f"), ("1", "f"), ("2", "f")}
    assert result_nfa.input_symbols == {"00", "01", "10", "11"}
    expected_transitions = {
        ("q0", "s"): {"10": {("-1", "f")}, "00": {("0", "f")}},
        ("-1", "f"): {"11": {("0", "f")}, "01": {("-1", "f")}, "10": {("-1", "f")}},
        ("0", "f"): {"01": {("1", "f")}, "10": {("1", "f")}, "11": {("2", "f")}, "00": {("0", "f")}},
        ("1", "f"): {"00": {("2", "f")}},
    }
    assert expected_transitions.keys() == result_nfa.transitions.keys()

    for key in expected_transitions:
        assert expected_transitions[key] == result_nfa.transitions[key]

    assert result_nfa.initial_state == ("q0", "s")
    assert result_nfa.final_states == {("2", "f")}

    pass
