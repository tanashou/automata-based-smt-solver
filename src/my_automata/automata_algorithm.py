from itertools import product
from src.my_automata.my_automata import MutableNFA as NFA
from typing import List, AbstractSet


def binary_strings(n) -> AbstractSet[str]:
    # Generate all possible combinations of 0 and 1 of length n
    combinations = product("01", repeat=n)
    # Join the tuples to form binary strings
    return set("".join(x) for x in combinations)


def binary_strings_with_wildcard(mask: List[bool]) -> AbstractSet[str]:
    """
    Generates binary strings with a wildcard (*) inserted at specified positions based on a mask.

    Args:
        mask: A list of booleans where True indicates that the corresponding position should be kept,
              and False indicates that the position should be removed.

    Returns:
        A set of binary strings with the wildcard (*) inserted at appropriate positions based on the mask.
    """

    # Generate combinations of "01" for the positions to keep
    combinations = list(product("01", repeat=mask.count(True)))
    # Convert combinations into binary strings
    binary_strings = ["".join(x) for x in combinations]

    # Iterate over the mask and insert the wildcard (*) at specified positions
    for i, is_masked in enumerate(mask):
        if not is_masked:
            binary_strings = [s[:i] + "*" + s[i:] for s in binary_strings]

    return binary_strings


def inner(vector1, vector2) -> int:
    if len(vector1) != len(vector2):
        raise ValueError("Vectors must have the same length")

    result = 0
    for i in range(len(vector1)):
        result += int(vector1[i]) * int(vector2[i])

    return result


def inner_with_wildcard(vector1, vector2) -> int:
    if len(vector1) != len(vector2):
        raise ValueError("Vectors must have the same length")

    result = 0
    for i in range(len(vector1)):
        # Skip calculation if either element is a wildcard (*)
        if vector1[i] == "*" or vector2[i] == "*":
            continue
        result += int(vector1[i]) * int(vector2[i])

    return result


"""
a: coefficients of the linear equation
c: constant of the linear equation
"""


def eq_to_nfa(a: List[int], c: int) -> NFA:
    initial_state = "q0"
    nfa = NFA(
        states={initial_state, str(c)},
        input_symbols=binary_strings(len(a)),
        transitions=dict(),
        initial_state=initial_state,
        final_states=set([str(c)]),
    )

    work_list = [c]  # TODO: queue を使用するか検討

    while work_list:
        current_state = work_list.pop()
        for symbol in nfa.input_symbols:  # b もワイルドカードを含む
            dot = inner(a, symbol)
            if (previous_state := 0.5 * (current_state - dot)).is_integer():
                previous_state = int(previous_state)
                if str(previous_state) not in nfa.states:
                    nfa.add_state(str(previous_state))
                    work_list.append(previous_state)
                nfa.add_transition(str(previous_state), symbol, str(current_state))
            if current_state == -dot:
                nfa.add_transition(initial_state, symbol, str(current_state))
                # return nfa # TODO: オートマトンを完全に作るかどうか

    return nfa


def neq_to_nfa(a: List[int], c: int):
    pass


# wildcard を使用するため、自作する必要がある
def nfa_intersection(nfa1: NFA, nfa2: NFA) -> NFA:
    initial_state = (nfa1.initial_state, nfa2.initial_state)
    nfa = NFA(
        states=set(),
        input_symbols=nfa1.input_symbols.intersection(nfa2.input_symbols),
        transitions=dict(),
        initial_state=initial_state,
        final_states=set(),
    )

    work_list: List[str] = [initial_state]

    if not nfa.input_symbols:
        raise ValueError("The given NFAs have no common input symbols")

    while work_list:
        current_state1, current_state2 = work_list.pop()
        nfa.add_state((current_state1, current_state2))
        if current_state1 in nfa1.final_states and current_state2 in nfa2.final_states:
            nfa.add_final_state((current_state1, current_state2))
        for symbol in nfa.input_symbols:
            next_states1 = nfa1.find_transitions_from_keys(current_state1, symbol)
            next_states2 = nfa2.find_transitions_from_keys(current_state2, symbol)
            for next_state1, next_state2 in set(product(next_states1, next_states2)):
                nfa.add_transition((current_state1, current_state2), symbol, (next_state1, next_state2))
                if (next_state1, next_state2) not in nfa.states:
                    work_list.append((next_state1, next_state2))

    return nfa
