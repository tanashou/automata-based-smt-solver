import itertools
from src.my_automata.mutable_nfa import SymbolT, NFAStateT, NFAPathT, NFATransitionT

WILDCARD = "*"


def binary_strings_with_wildcard(mask: list[bool]) -> set[str]:
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


def dot_product_with_wildcard(coefs: list[str], symbol: SymbolT) -> int:
    if len(coefs) != len(symbol):
        raise ValueError("The length of the mask must be equal to the length of the coefficients")

    result = 0

    for v1, v2 in zip(coefs, symbol):
        if v2 != WILDCARD:
            result += int(v1) * int(v2)
    return result


def apply_mask(pattern: SymbolT, mask: list[bool]) -> SymbolT:
    if len(pattern) != len(mask):
        raise ValueError("The length of the mask must be equal to the length of the pattern")

    result = ""
    for i in range(len(mask)):
        if mask[i]:
            result += pattern[i]
        else:
            result += WILDCARD

    return result


def symbol_intersection(symbol1: SymbolT, symbol2: SymbolT) -> SymbolT:
    if len(symbol1) != len(symbol2):
        raise ValueError("Symbols must have the same length")

    result = ""
    for s1, s2 in zip(symbol1, symbol2):
        if s1 != s2 and WILDCARD not in (s1, s2):
            return ""
        result += s1 if s1 != WILDCARD else s2
    return result


def intersection_containing_wildcard(symbols1: set[SymbolT], symbols2: set[SymbolT]) -> set[SymbolT]:
    """
    example: if '01*' and '0*0' are given, add '010' to result
    """
    result = set()
    for s1, s2 in itertools.product(symbols1, symbols2):
        s = symbol_intersection(s1, s2)
        if s:
            result.add(s)

    return result
