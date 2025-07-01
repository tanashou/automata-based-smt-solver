from collections.abc import Generator
from dataclasses import dataclass
from itertools import product

from pysmt.fnode import FNode

from absmt.automata.msbf_alphabet_symbol import (
    MSBFAlphabetSymbol,
)


@dataclass(slots=True)
class MSBFAlphabet:
    all_vars: list[FNode]
    used_vars: list[FNode]

    def __post_init__(self) -> None:
        if not set(self.used_vars).issubset(set(self.all_vars)):
            msg = "used_vars must be a subset of all_vars"
            raise ValueError(msg)
        self.all_vars = sorted(self.all_vars, key=lambda x: str(x))
        self.used_vars = sorted(self.used_vars, key=lambda x: str(x))

    def has_same_symbols(self, other: "MSBFAlphabet") -> bool:
        return self.all_vars == other.all_vars

    def symbol_generator(self) -> Generator[MSBFAlphabetSymbol]:
        mask = "".join("1" if var in self.used_vars else "0" for var in self.all_vars)
        choices = [("0", "1") if ch == "1" else ("0",) for ch in mask]
        for bits in product(*choices):
            yield MSBFAlphabetSymbol("".join(bits), mask)

    @staticmethod
    def union_alphabet(a1: "MSBFAlphabet", a2: "MSBFAlphabet") -> "MSBFAlphabet":
        if a1.all_vars != a2.all_vars:
            msg = "Alphabets must have the same all_vars"
            raise ValueError(msg)
        union_used_vars = sorted(set(a1.used_vars) | set(a2.used_vars))

        return MSBFAlphabet(a1.all_vars, union_used_vars)

    def decode_symbol(
        self, symbols: list[MSBFAlphabetSymbol]
    ) -> dict[FNode, int | None]:
        def twos_comp(val: int, bits: int) -> int:
            if (val & (1 << (bits - 1))) != 0:
                val = val - (1 << bits)
            return val

        result: dict[FNode, int | None] = {}
        symbol_strs = [str(s) for s in symbols]
        transposed = ["".join(chars) for chars in zip(*symbol_strs, strict=True)]

        for var, bits_str in zip(self.all_vars, transposed, strict=True):
            if "*" in bits_str:
                result[var] = None
                continue

            result[var] = twos_comp(int(bits_str, 2), len(bits_str))
        return result
