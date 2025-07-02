from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import spot

from absmt.automata.msbf_alphabet import MSBFAlphabet
from absmt.automata.msbf_to_bdd_encoder import MSBFToBDDEncoder
from absmt.automata.nfa import NFAStateT, NFATransitionsT

if TYPE_CHECKING:
    from absmt.automata.nfa import NFA


@dataclass
class SpotNFA:
    """Wrapper class for converting NFA components to Spot automaton."""

    states: set[NFAStateT]
    alphabet: MSBFAlphabet
    transitions: NFATransitionsT
    initial_state: NFAStateT
    final_states: set[NFAStateT]

    bdd_encoder: MSBFToBDDEncoder

    _bdict: Any = None  # spot.bdd_dict | None
    spot_automaton: Any = None  # spot.twa_graph | None
    _state_map: dict[NFAStateT, int] = field(default_factory=dict, init=False)
    _bdd_var_ids: dict[str, Any] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        """Initialize the Spot automaton after creation."""
        self._create_automaton()
        self.bdd_encoder.register_ap(self.spot_automaton)
        self._set_acceptance_condition()
        self._add_states()
        self._set_initial_state()
        self._add_transitions()

    def _create_automaton(self) -> None:
        """Create BDD dictionary and Spot automaton."""
        self._bdict = spot.make_bdd_dict()
        self.spot_automaton = spot.make_twa_graph(self._bdict)

    def _add_states(self) -> None:
        """Add states to the automaton."""
        self._state_map = {}
        state_list = list(self.states)

        if state_list:
            # Add required number of states
            self.spot_automaton.new_states(len(state_list))  # type: ignore[attr-defined]
            for i, state in enumerate(state_list):
                self._state_map[state] = i

    def _set_initial_state(self) -> None:
        """Set the initial state of the automaton."""
        if self._state_map is not None and self.initial_state in self._state_map:
            initial_state_id = self._state_map[self.initial_state]
            self.spot_automaton.set_init_state(initial_state_id)  # type: ignore[attr-defined]

    def _set_acceptance_condition(self) -> None:
        """Set acceptance condition for Büchi automaton."""
        # 受理状態集合の数なので第一引数は 1
        # 無限語、有限語ともに受理したいので第二引数は "Inf(0) | Fin(0)"
        # 受理集合は 0
        self.spot_automaton.set_acceptance(1, "Inf(0) | Fin(0)")  # type: ignore[attr-defined]

    def _add_transitions(self) -> None:
        """Add transitions to the automaton."""
        for state_from, transitions in self.transitions.items():
            state_from_id = self._state_map[state_from]
            for symbol, state_to_set in transitions.items():
                for state_to in state_to_set:
                    state_to_id = self._state_map[state_to]
                    bdd = self.bdd_encoder.symbol_to_bdd(symbol)
                    if state_to in self.final_states:
                        # 受理状態に入る遷移に集合0を割り当てる
                        self.spot_automaton.new_edge(
                            state_from_id, state_to_id, bdd, [0]
                        )
                    else:
                        self.spot_automaton.new_edge(state_from_id, state_to_id, bdd)

    def to_hoa(self) -> str:
        """Convert the automaton to HOA format string."""
        return self.spot_automaton.to_str("hoa")  # type: ignore[attr-defined]

    def to_dot(self) -> str:
        """Convert the automaton to DOT format string."""
        return self.spot_automaton.to_str("dot")  # type: ignore[attr-defined]

    def accepts(self, word: str) -> bool:
        """Check if the automaton accepts a given word."""
        msg = "Word acceptance checking not yet implemented"
        raise NotImplementedError(msg)

    def minimize(self) -> "SpotNFA":
        """Return a minimized version of this automaton."""
        msg = "Minimization not yet implemented"
        raise NotImplementedError(msg)

    @classmethod
    def from_nfa(cls, nfa: "NFA") -> "SpotNFA":
        """Create SpotNFA from an NFA object.

        Args:
            nfa: NFA object to convert

        Returns:
            SpotNFA: New SpotNFA instance

        """
        raise NotImplementedError

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
