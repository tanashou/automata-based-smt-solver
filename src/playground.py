from src.my_automata.my_automata import MutableNFA as NFA
from src.my_automata.automata_algorithm import *

nfa = NFA(
    states={"q0", "q1", "q2"},
    input_symbols={"a", "b"},
    transitions={
        "q0": {"a": {"q1"}},
        # Use '' as the key name for empty string (lambda/epsilon) transitions
        "q1": {"a": {"q1"}, "": {"q2"}},
        "q2": {"b": {"q0"}},
    },
    initial_state="q0",
    final_states={"q1"},
)

nfa2 = NFA(
    states={"q0", "q1", "q200"},
    input_symbols={"a", "b"},
    transitions={
        "q0": {"a": {"q1"}},
        # Use '' as the key name for empty string (lambda/epsilon) transitions
        "q1": {"a": {"q1"}, "": {"q200"}},
        "q200": {"b": {"q0"}},
    },
    initial_state="q0",
    final_states={"q1"},
)

coefs = [1, -1, 1]
mask1 = [True, True, False]
mask2 = [True, False, True]

complete_nfa1 = eq_to_nfa(coefs, 2, mask1)
complete_nfa2 = eq_to_nfa(coefs, 5, mask2)
partial_nfa1 = eq_to_nfa(coefs, 2, mask1, create_all=False)
partial_nfa2 = eq_to_nfa(coefs, 5, mask2, create_all=False)


complete_nfa = nfa_intersection(complete_nfa1, complete_nfa2, mask1, mask2)
partial_nfa = nfa_intersection(partial_nfa1, partial_nfa2, mask1, mask2)
complete_nfa.show_diagram(path="image/complete1.png")
partial_nfa.show_diagram(path="image/partial1.png")
