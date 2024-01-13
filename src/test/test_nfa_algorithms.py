from random import sample
import pytest
from my_smt_solver import AutomataBuilder, NFA as NFA, PresburgerArithmetic, Relation
from collections import defaultdict


# Define a fixture for creating NFAs with common structure
@pytest.fixture
def sample_NFAs() -> tuple[NFA, NFA]:
    p = PresburgerArithmetic(terms=[("x", 1), ("y", 1)], relation=Relation.EQ, const=2)
    coefs = [1, 1]
    bld1 = AutomataBuilder(coefs, p, create_all=True)
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

@pytest.fixture
def sample_neq_NFAs() -> NFA:
    p = PresburgerArithmetic(terms=[("z_neq", 1)], relation=Relation.NEQ, const=0)
    coefs = [0, 0, 0, 1]
    bld = AutomataBuilder(coefs, p, create_all=True)
    bld.neq_to_nfa()
    return bld.nfa


def test_nfa_intersection(sample_NFAs: tuple[NFA, NFA]) -> None:
    """
    x + z = 2 and x >= 0
    """
    n1, n2 = sample_NFAs

    result_nfa = n1.intersection(n2)

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

def test_neq_to_nfa(sample_neq_NFAs: NFA) -> None:
    assert sample_neq_NFAs.states == {"q0", "0"}
    assert sample_neq_NFAs.input_symbols == {"***0", "***1"}
    expected_transitions = {
        "q0": {"***0": {"q0"}, "***1": {"0"}},
        "0": {"***1": {"0"}, "***0": {"0"}},
    }
    assert sample_neq_NFAs.transitions == expected_transitions
