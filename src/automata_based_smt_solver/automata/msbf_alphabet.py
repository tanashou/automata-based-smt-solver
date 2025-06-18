from collections.abc import Generator
from dataclasses import dataclass
from itertools import product

from pysmt.fnode import FNode

from automata_based_smt_solver.automata.msbf_alphabet_symbol import (
    MSBFAlphabetSymbol,
)


@dataclass(slots=True)
class MSBFAlphabet:
    all_vars: list[FNode]
    used_vars: list[FNode]

    def __post_init__(self) -> None:
        self.all_vars = sorted(self.all_vars)
        self.used_vars = sorted(self.used_vars)

    def has_same_symbols(self, other: "MSBFAlphabet") -> bool:
        return self.all_vars == other.all_vars

    def symbol_generator(self) -> Generator[MSBFAlphabetSymbol]:
        mask = "".join("1" if var in self.used_vars else "0" for var in self.all_vars)
        choices = [("0", "1") if ch == "1" else ("0",) for ch in mask]
        for bits in product(*choices):
            yield MSBFAlphabetSymbol("".join(bits), mask)

    @staticmethod
    def intersect_alphabet(a1: "MSBFAlphabet", a2: "MSBFAlphabet") -> "MSBFAlphabet":
        if a1.all_vars != a2.all_vars:
            msg = "Alphabets must have the same all_vars"
            raise ValueError(msg)
        intersected_used_vars = sorted(set(a1.used_vars) & set(a2.used_vars))

        return MSBFAlphabet(a1.all_vars, intersected_used_vars)

    def decode_symbol(
        self, symbols: list[MSBFAlphabetSymbol]
    ) -> dict[FNode, int | None]:
        result: dict[FNode, int | None] = {}
        symbol_strs = [str(s) for s in symbols]
        transposed = ["".join(chars) for chars in zip(*symbol_strs, strict=True)]

        for var, bits in zip(self.all_vars, transposed, strict=False):
            if "*" in bits:
                result[var] = None
            k = len(bits) - 1
            first_bit = bits[0]
            if first_bit == "0":
                # unsigned: sum bi*2^(k-i)
                value = sum(int(b) * (2 ** (k - i)) for i, b in enumerate(bits))
            else:
                # signed: -1*2^k + sum_{i=1}^k bi*2^{k-i}
                value = -1 * (2**k) + sum(
                    int(b) * (2 ** (k - i)) for i, b in enumerate(bits[1:], 1)
                )
            result[var] = value
        return result
