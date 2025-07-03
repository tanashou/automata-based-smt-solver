import logging
from dataclasses import dataclass, field
from typing import Any

import buddy
import spot

from absmt.automata.msbf_alphabet import MSBFAlphabet
from absmt.automata.msbf_alphabet_symbol import MSBFAlphabetSymbol
from absmt.automata.nfa import NFA, NFAStateT, NFATransitionsT

logger = logging.getLogger(__name__)


@dataclass
class SpotNFA:
    """Wrapper class for converting NFA components to Spot automaton."""

    states: set[NFAStateT]
    alphabet: MSBFAlphabet
    transitions: NFATransitionsT
    initial_state: NFAStateT
    final_states: set[NFAStateT]
    bdd_dict: Any  # spot.bdd_dict

    spot_automaton: Any = field(
        default_factory=lambda: None,
        init=False,
    )  # spot.twa_graph | None
    _state_map: dict[NFAStateT, int] = field(default_factory=dict, init=False)
    _bdd_var_str_to_id: dict[str, Any] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        """Initialize the Spot automaton after creation."""
        self._create_automaton()
        self._register_ap()
        self._add_states()
        self._set_initial_state()
        self._add_transitions()

    def _create_automaton(self) -> None:
        """Create BDD dictionary and Spot automaton."""
        self.spot_automaton = spot.make_twa_graph(self.bdd_dict)
        # Set the acceptance condition of the automaton to Inf(0)
        self.spot_automaton.set_buchi()
        # Pretend this is state-based acceptance
        self.spot_automaton.prop_state_acc(True)  # noqa: FBT003

    def _register_ap(self) -> None:
        """Register atomic propositions for each variable in the BDD."""
        for var in self.alphabet.used_vars:
            bdd_var_id = self.spot_automaton.register_ap(str(var))
            self._bdd_var_str_to_id[str(var)] = bdd_var_id

    def _add_states(self) -> None:
        """Add states to the automaton."""
        self._state_map = {}

        if self.states:
            # Add required number of states
            self.spot_automaton.new_states(len(self.states))
            # spot.aut の状態と NFA の状態を対応させるためのマップを作成
            for i, state in enumerate(self.states):
                self._state_map[state] = i

    def _set_initial_state(self) -> None:
        """Set the initial state of the automaton."""
        if self._state_map is not None and self.initial_state in self._state_map:
            initial_state_id = self._state_map[self.initial_state]
            self.spot_automaton.set_init_state(initial_state_id)

    def _add_transitions(self) -> None:
        """Add transitions to the automaton."""
        for state_from, transitions in self.transitions.items():
            state_from_id = self._state_map[state_from]
            is_state_from_final = state_from in self.final_states

            # 受理状態からの遷移全てを受理条件に追加
            for symbol, state_to_set in transitions.items():
                for state_to in state_to_set:
                    state_to_id = self._state_map[state_to]

                    formula = self.symbol_to_formula(symbol)

                    if is_state_from_final:
                        self.spot_automaton.new_edge(
                            state_from_id, state_to_id, formula, [0]
                        )
                    else:
                        self.spot_automaton.new_edge(
                            state_from_id, state_to_id, formula
                        )

        # Buchi オートマトンに変換するため、無限語を受理できるようにする
        for final_state in self.final_states:
            if self.transitions.get(final_state) is None:
                # If there are no transitions from the final state, create a self-loop
                final_state_id = self._state_map[final_state]
                self.spot_automaton.new_edge(
                    final_state_id,
                    final_state_id,
                    buddy.bddtrue,
                )

    def symbol_to_formula(self, symbol: MSBFAlphabetSymbol) -> object:
        """Convert MSBF alphabet symbol to formula.

        Args:
            symbol: The MSBF alphabet symbol to convert

        Returns:
            Formula representing the symbol

        """
        # Start with True (bddtrue)
        result = buddy.bddtrue

        symbol_str = str(symbol)
        for i, bit in enumerate(symbol_str):
            var_name = str(self.alphabet.all_vars[i])

            if bit == "1":
                bdd_var_id = self._bdd_var_str_to_id[var_name]
                # Bit is 1 means variable is True
                result = result & buddy.bdd_ithvar(bdd_var_id)
            elif bit == "0":
                bdd_var_id = self._bdd_var_str_to_id[var_name]
                # Bit is 0 means variable is False (negated)
                result = result & (-buddy.bdd_ithvar(bdd_var_id))
            # Skip wildcards

        return result

    def to_hoa(self) -> str:
        """Convert the automaton to HOA format string."""
        return self.spot_automaton.to_str("hoa")

    def to_dot(self) -> str:
        """Convert the automaton to DOT format string."""
        return self.spot_automaton.to_str("dot")

    def accepts(self, word: str) -> bool:
        """Check if the automaton accepts a given word."""
        msg = "Word acceptance checking not yet implemented"
        raise NotImplementedError(msg)

    def minimize(self) -> "SpotNFA":
        """Return a minimized version of this automaton."""
        msg = "Minimization not yet implemented"
        raise NotImplementedError(msg)

    @classmethod
    def from_nfa(cls, nfa: "NFA", bdd_dict: Any) -> "SpotNFA":  # noqa: ANN401
        """Create SpotNFA from an NFA object.

        Args:
            nfa: NFA object to convert
            bdd_dict: BDD dictionary to use for the Spot automaton

        Returns:
            SpotNFA: New SpotNFA instance

        """
        return cls(
            nfa.states,
            nfa.input_symbols,
            nfa.transitions,
            nfa.initial_state,
            nfa.final_states,
            bdd_dict,
        )

    def __str__(self) -> str:
        """Return string representation showing the HOA format."""
        return self.to_hoa()

    @staticmethod
    def has_common_language(*nfas: "SpotNFA") -> bool:
        """Check if all given NFAs have a common language.

        Args:
            *nfas: SpotNFA instances to check

        Returns:
            bool: True if all NFAs have a common language, False otherwise

        """
        if not nfas:
            logger.debug("No NFAs provided, returning True for common language check.")
            return True  # Empty set has trivially common language

        if len(nfas) == 1:
            return not nfas[0].spot_automaton.is_empty()  # type: ignore[attr-defined]

        # Initialize product with first automaton
        product_aut = nfas[0].spot_automaton

        # Calculate product with remaining automata
        for nfa in nfas[1:]:
            product_aut = spot.product(product_aut, nfa.spot_automaton)  # type: ignore[attr-defined]

            # Early termination: return False if product becomes empty
            if product_aut.is_empty():  # type: ignore[attr-defined]
                return False

        return not product_aut.is_empty()  # type: ignore[attr-defined]
