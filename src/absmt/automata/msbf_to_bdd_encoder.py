from dataclasses import dataclass, field
from typing import Any

import buddy

from absmt.automata.msbf_alphabet import MSBFAlphabet
from absmt.automata.msbf_alphabet_symbol import MSBFAlphabetSymbol


@dataclass
class MSBFToBDDEncoder:
    msbf_alphabet: MSBFAlphabet
    _bdd_ithvars: dict[str, Any] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        for var in self.msbf_alphabet.all_vars:
            self._bdd_ithvars[str(var)] = buddy.bdd_ithvar(str(var))

    def symbol_to_bdd(self, symbol: MSBFAlphabetSymbol) -> object:
        """Convert MSBF alphabet symbol to BDD condition.

        Args:
            symbol: The MSBF alphabet symbol to convert

        Returns:
            BDD condition representing the symbol

        """
        # Start with True (bddtrue)
        result = buddy.bddtrue

        symbol_str = str(symbol)
        for i, bit in enumerate(symbol_str):
            var_name = str(self.msbf_alphabet.all_vars[i])
            bdd_var = self._bdd_ithvars[var_name]

            if bit == "1":
                # Bit is 1 means variable is True
                result = result & bdd_var
            elif bit == "0":
                # Bit is 0 means variable is False (negated)
                result = result & (~bdd_var)
            # Skip wildcards

        return result
