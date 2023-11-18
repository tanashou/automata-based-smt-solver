from src.my_automata.my_automata import MutableNFA as NFA
from automata.fa.nfa import NFA as BaseNFA
from src.my_automata.automata_algorithm import *

from collections import defaultdict


# Initialize the defaultdict
transitions = defaultdict(lambda: defaultdict(set))

# Add values to the dictionary
transitions["q0"]["a"].add("q1")
transitions["q1"]["a"].add("q1")
transitions["q1"][""].add("q2")
transitions["q2"]["b"].add("q0")


nfa = NFA(
    states={"q0", "q1", "q2"},
    input_symbols={"a", "b"},
    transitions=transitions,
    initial_state="q0",
    final_states={"q1"},
)

coefs = [1, -1, 1]
mask1 = [True, True, False]
mask2 = [True, False, True]

# complete_nfa1 = AutomataBuilder(coefs, 2, 'equal', mask1, create_all=True)
# complete_nfa2 = AutomataBuilder(coefs, 5, 'equal', mask2, create_all=True)
partial_nfa1 = AutomataBuilder(coefs, 2, "equal", mask1, create_all=False)
partial_nfa2 = AutomataBuilder(coefs, 5, "equal", mask2, create_all=False)

# complete_nfa1.next()
# complete_nfa2.next()
# partial_nfa1.next()
# partial_nfa2.next()

count = 0
while partial_nfa1.next():
    partial_nfa1.nfa.show_diagram(path=f"image/partial1_{count}.png")
    count += 1

count = 0
while partial_nfa2.next():
    partial_nfa2.nfa.show_diagram(path=f"image/partial2_{count}.png")
    count += 1

intersection_nfa = nfa_intersection(partial_nfa1.nfa, partial_nfa2.nfa, mask1, mask2)
intersection_nfa.show_diagram(path="image/intersection.png")


# # complete_nfa = nfa_intersection(complete_nfa1.nfa, complete_nfa2.nfa, mask1, mask2)
# partial_nfa = nfa_intersection(partial_nfa1.nfa, partial_nfa2.nfa, mask1, mask2)
# # complete_nfa.show_diagram(path="image/complete1.png")
# partial_nfa.show_diagram(path="image/partial1.png")
