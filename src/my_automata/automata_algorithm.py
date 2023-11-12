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


def eq_to_nfa(a, c: int):
    initial_state = "q0"
    states = {initial_state, str(c)}
    input_symbols = binary_strings(len(a))
    transitions = dict()
    final_states = set([str(c)])
    work_list = [c]  # TODO: queue を使用するか検討
    nfa = NFA(states, input_symbols, transitions, initial_state, final_states)

    # TODO: 変数の名前を変更する。q とか q_prime とか出なく、state など具体的な名前にする。
    while work_list:
        q = work_list.pop()
        for b in input_symbols:  # b もワイルドカードを含む
            dot = dot_product(a, b)
            if (q_prime := 0.5 * (q - dot)).is_integer():
                q_prime = int(q_prime)
                if str(q_prime) not in states:
                    nfa.add_state(str(q_prime))
                    work_list.append(q_prime)
                nfa.add_transition(str(q_prime), b, str(q))
            if q == -dot:
                nfa.add_transition(initial_state, b, str(q))
                # return nfa # TODO: オートマトンを完全に作るかどうか

    return nfa
