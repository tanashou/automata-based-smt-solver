import itertools
from src.my_automata.my_automata import MutableNFA as NFA
from typing import List, Set

WILDCARD = "*"


def binary_strings(n) -> Set[str]:
    # Generate all possible combinations of 0 and 1 of length n
    combinations = itertools.product("01", repeat=n)
    # Join the tuples to form binary strings
    return set("".join(x) for x in combinations)


def binary_strings_with_wildcard(mask: List[bool]) -> Set[str]:
    """
    Generates binary strings with a wildcard (*) inserted at specified positions based on a mask.

    Args:
        mask: A list of booleans where True indicates that the corresponding position should be kept,
              and False indicates that the position should be removed.

    Returns:
        A set of binary strings with the wildcard (*) inserted at appropriate positions based on the mask.
    """

    # Generate combinations of "01" for the positions to keep
    combinations = list(itertools.product("01", repeat=mask.count(True)))
    # Convert combinations into binary strings
    binary_strings = {"".join(x) for x in combinations}

    # Iterate over the mask and insert the wildcard (*) at specified positions
    for i, is_masked in enumerate(mask):
        if not is_masked:
            binary_strings = {s[:i] + WILDCARD + s[i:] for s in binary_strings}

    return binary_strings


def dot_product(vector1, vector2) -> int:
    if len(vector1) != len(vector2):
        raise ValueError("Vectors must have the same length")

    result = 0
    for i in range(len(vector1)):
        result += int(vector1[i]) * int(vector2[i])

    return result


def dot_product_with_wildcard(vector1, vector2) -> int:
    if len(vector1) != len(vector2):
        raise ValueError("Vectors must have the same length")

    result = 0
    for i in range(len(vector1)):
        # Skip calculation if either element is a wildcard (*)
        if vector1[i] == WILDCARD or vector2[i] == WILDCARD:
            continue
        result += int(vector1[i]) * int(vector2[i])

    return result


"""
coefs: all the coefficients of the linear equation
const: constant of the linear equation
"""


def eq_to_nfa(coefs: List[int], const: int, mask: List[bool]) -> NFA:
    if len(coefs) != len(mask):
        raise ValueError("The length of the mask must be equal to the length of the coefficients")

    initial_state = "q0"
    nfa = NFA(
        states={initial_state, str(const)},
        input_symbols=binary_strings_with_wildcard(mask),
        transitions=dict(),
        initial_state=initial_state,
        final_states=set([str(const)]),
    )
    work_list = [const]  # TODO: queue を使用するか検討

    while work_list:
        current_state = work_list.pop()
        for symbol in nfa.input_symbols:  # b もワイルドカードを含む
            dot = dot_product_with_wildcard(coefs, symbol)
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
# TODO: mask をクラスで管理する
def nfa_intersection(nfa1: NFA, nfa2: NFA, mask1, mask2) -> NFA:
    def apply_mask(pattern, mask) -> str:
        if len(pattern) != len(mask):
            raise ValueError("The length of the mask must be equal to the length of the pattern")

        result = ""
        for i in range(len(mask)):
            if mask[i]:
                result += pattern[i]
            else:
                result += WILDCARD

        return result

    def symbol_intersection(symbol1, symbol2):
        if len(symbol1) != len(symbol2):
            raise ValueError("Symbols must have the same length")

        result = ""
        for s1, s2 in zip(symbol1, symbol2):
            if s1 != s2 and WILDCARD not in (s1, s2):
                return ""
            result += s1 if s1 != WILDCARD else s2
        return result

    def intersection_containing_wildcard(symbols1, symbols2) -> Set[str]:
        """
        '01*' と '0*0'があった時、'010'をresultに追加する
        """
        result = set()
        for s1, s2 in itertools.product(symbols1, symbols2):
            s = symbol_intersection(s1, s2)
            if s:
                result.add(s)

        return result

    initial_state = (nfa1.initial_state, nfa2.initial_state)
    nfa = NFA(
        states=set(),
        input_symbols=intersection_containing_wildcard(nfa1.input_symbols, nfa2.input_symbols),
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
            next_states1 = nfa1.find_transitions_from_keys(current_state1, apply_mask(symbol, mask1))
            next_states2 = nfa2.find_transitions_from_keys(current_state2, apply_mask(symbol, mask2))
            for next_state1, next_state2 in set(itertools.product(next_states1, next_states2)):
                nfa.add_transition((current_state1, current_state2), symbol, (next_state1, next_state2))
                if (next_state1, next_state2) not in nfa.states:
                    work_list.append((next_state1, next_state2))

    return nfa
