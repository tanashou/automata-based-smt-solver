from dataclasses import dataclass, field
from typing import Any

import buddy

from absmt.automata.msbf_alphabet import MSBFAlphabet
from absmt.automata.msbf_alphabet_symbol import MSBFAlphabetSymbol


@dataclass
class MSBFToBDDEncoder:
    msbf_alphabet: MSBFAlphabet
    _bdd_var_index_from_var_name: dict[str, Any] = field(
        default_factory=dict, init=False
    )

    def __post_init__(self) -> None:
        for var in self.msbf_alphabet.all_vars:
            self._bdd_var_index_from_var_name[str(var)] = buddy.bdd_ithvar(str(var))

    # spot_automaton:: spot.twa_graph
    def register_ap(self, spot_automaton: Any) -> None:  # noqa: ANN401
        """Register atomic propositions for each variable in the BDD."""
        for var in self.msbf_alphabet.all_vars:
            # Register each variable as an atomic proposition
            bdd_var_index = spot_automaton.register_ap(str(var))
            self._bdd_var_index_from_var_name[str(var)] = bdd_var_index

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
            bdd_var_index = self._bdd_var_index_from_var_name[var_name]

            if bit == "1":
                # Bit is 1 means variable is True
                result = result & buddy.bdd_ithvar(bdd_var_index)
            elif bit == "0":
                # Bit is 0 means variable is False (negated)
                result = result & (~buddy.bdd_ithvar(bdd_var_index))
            # Skip wildcards

        return result
