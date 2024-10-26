from collections import defaultdict
from itertools import product

from .type import SymbolT

WILDCARD = "*"


# 全体の変数のうち、coefsに含まれる箇所を0, 1、ないものを*とした全ての文字列を生成
def make_binary_wildcard_strings(
    var_index_map: dict[str, int], coefs: defaultdict[str, int]
) -> set[str]:
    all_vars = list(var_index_map.keys())
    coef_vars = [var for var in all_vars if var in coefs]
    combinations = product("01", repeat=len(coef_vars))
    result = set()

    for combination in combinations:
        encoded = [WILDCARD] * len(all_vars)
        for index, var in enumerate(coef_vars):
            encoded[var_index_map[var]] = combination[index]

        result.add("".join(encoded))

    return result


def dot_product_with_wildcard(var_index_map: dict[str, int], coefs: defaultdict[str, int], symbol: str) -> int:
    result = 0
    # 0 * WILDCARD か (0以外の数値) * (0 or 1) の場合のみ出てくるので、片方のみ判定すればいい
    for key, value in coefs.items():
        if symbol[var_index_map[key]] == WILDCARD:
            continue
        result += value * int(symbol[var_index_map[key]])
    return result


def apply_mask(pattern: SymbolT, mask: list[bool]) -> SymbolT:
    if len(pattern) != len(mask):
        raise ValueError(
            "The length of the mask must be equal to the length of the pattern"
        )

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
    for s1, s2 in zip(symbol1, symbol2, strict=False):
        if s1 != s2 and WILDCARD not in (s1, s2):
            return ""
        result += s1 if s1 != WILDCARD else s2
    return result


def intersection_containing_wildcard(
    symbols1: set[SymbolT], symbols2: set[SymbolT]
) -> set[SymbolT]:
    """example: if '01*' and '0*0' are given, add '010' to result"""
    result = set()
    for s1, s2 in product(symbols1, symbols2):
        s = symbol_intersection(s1, s2)
        if s:
            result.add(s)

    return result


def decode_symbols_to_int(symbols: list[SymbolT]) -> list[int]:
    def twos_complement_to_decimal(binary_str: str) -> int:
        if WILDCARD in binary_str:
            raise ValueError("The given string must not contain wildcard")

        decimal_value = int(binary_str, 2)

        # If the number is negative, compute its negative value directly
        if binary_str[0] == "1":  # If the number is negative
            num_bits = len(binary_str)
            decimal_value -= 1 << num_bits

        return decimal_value

    # decode symbols to complement binary strings
    transposed = map("".join, zip(*symbols, strict=False))
    return list(map(twos_complement_to_decimal, transposed))
