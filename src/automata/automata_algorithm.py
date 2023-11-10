from itertools import product
from src.automata.automata import NFA


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


def eq_to_nfa(a, c):
    states = {"q0", f"{c}"}
    input_symbols = binary_strings(len(a))
    transitions = {}
    final_states = {c}
    work_list = [c]

    while work_list:
        q = work_list.pop()
        for b in input_symbols:  # b もワイルドカードを含む
            dot = dot_product(a, b)
            q_prime = 0.5 * (q - dot)
            if q_prime.is_integer():
                q_prime = int(q_prime)
                if q_prime not in states:
                    states.add(f'{q_prime}')
                    work_list.append(q_prime)
                transitions.setdefault(f"{q_prime}", {})[b] = {f"{q}"} # FIXME: うまく追加できない。
            if q == -dot:
                transitions.setdefault("q0", {})[b] = {f"{q}"}
                return NFA(states, input_symbols, transitions, "q0", final_states)

    return NFA(states, input_symbols, transitions, "q0", final_states)


print(eq_to_nfa([1, -1], 2).input_symbols)



