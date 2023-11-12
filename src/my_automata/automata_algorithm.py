from itertools import product
from src.my_automata.my_automata import MutableNFA as NFA


# TODO: ワイルドカードを使用できるようにする
def binary_strings(n):
    # Generate all possible combinations of 0 and 1 of length n
    combinations = product("01", repeat=n)
    # Join the tuples to form binary strings
    return ["".join(x) for x in combinations]


def dot_product(vector1, vector2):
    if len(vector1) != len(vector2):
        raise ValueError("Vectors must have the same length")

    result = 0
    for i in range(len(vector1)):
        result += int(vector1[i]) * int(vector2[i])

    return result


"""
a: coefficients of the linear equation
c: constant of the linear equation
"""


def eq_to_nfa(a, c: int):
    initial_state = "q0"
    states = {initial_state, str(c)}
    input_symbols = binary_strings(len(a))
    transitions = dict()
    final_states = set([str(c)])
    work_list = [c]  # TODO: queue を使用するか検討
    nfa = NFA(states, input_symbols, transitions, initial_state, final_states)

    while work_list:
        current_state = work_list.pop()
        for symbol in input_symbols:  # b もワイルドカードを含む
            dot = dot_product(a, symbol)
            if (previous_state := 0.5 * (current_state - dot)).is_integer():
                previous_state = int(previous_state)
                if str(previous_state) not in states:
                    nfa.add_state(str(previous_state))
                    work_list.append(previous_state)
                nfa.add_transition(str(previous_state), symbol, str(current_state))
            if current_state == -dot:
                nfa.add_transition(initial_state, symbol, str(current_state))
                # return nfa # TODO: オートマトンを完全に作るかどうか

    return nfa
