import itertools
from src.my_automata.my_automata import SymbolT, NFAStateT, NFAPathT, NFATransitionT

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


def dot_product_with_wildcard(self, coefs: list[str], symbol: SymbolT) -> int:
    result = 0

    for v1, v2 in zip(coefs, symbol):
        if v2 != WILDCARD:
            result += int(v1) * int(v2)
    return result
