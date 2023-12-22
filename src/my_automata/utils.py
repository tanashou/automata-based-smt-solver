import itertools
from src.my_automata.type import SymbolT, NFAStateT, NFAPathT, NFATransitionT

WILDCARD = "*"


def make_binary_wildcard_strings(coefs: list[int]) -> set[str]:
    # Generate combinations of "01" for the positions to keep
    count_not_zero = sum(1 for coef in coefs if coef != 0)
    combinations = list(itertools.product("01", repeat=count_not_zero))
    # Convert combinations into binary strings
    binary_wildcard_strings = {"".join(x) for x in combinations}

    # Iterate over the mask and insert the wildcard (*) at specified positions
    for i, coef in enumerate(coefs):
        if coef == 0:
            binary_wildcard_strings = {s[:i] + WILDCARD + s[i:] for s in binary_wildcard_strings}

    return binary_wildcard_strings


def dot_product_with_wildcard(coefs: list[int], symbol: SymbolT) -> int:
    if len(coefs) != len(symbol):
        raise ValueError("The length of the mask must be equal to the length of the coefficients")

    result = 0
    # 0 * WILDCARD か (0以外の数値) * (0 or 1) の場合のみ出てくるので、片方のみ判定すればいい
    for c, s in zip(coefs, symbol):
        if s != WILDCARD:
            result += c * int(s)
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


def decode_symbols_to_int(symbols: list[SymbolT]) -> list[str]:
    def twos_complement_to_decimal_with_wildcard(binary_str: str) -> str:
        if binary_str[0] == WILDCARD:
            return WILDCARD

        decimal_value = int(binary_str, 2)

        # If the number is negative, compute its negative value directly
        if binary_str[0] == "1":  # If the number is negative
            num_bits = len(binary_str)
            decimal_value -= 1 << num_bits

        return str(decimal_value)

    # decode symbols to complement binary strings
    transposed = map("".join, zip(*symbols))
    return list(map(twos_complement_to_decimal_with_wildcard, transposed))
