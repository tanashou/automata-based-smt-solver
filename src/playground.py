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

# test_nfa1 = eq_to_nfa([1, -2], 3)
# test_nfa2 = eq_to_nfa([1, -1], 2)
# nfa3 = nfa_intersection(test_nfa1, test_nfa2)
# nfa3.show_diagram(path='intersection.png')

print(dot_product_with_wildcard("1*1", "11*"))