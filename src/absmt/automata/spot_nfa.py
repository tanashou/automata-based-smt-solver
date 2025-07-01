from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import buddy
import spot

from absmt.automata.msbf_alphabet import MSBFAlphabet
from absmt.automata.msbf_alphabet_symbol import MSBFAlphabetSymbol
from absmt.automata.nfa import NFAStateT, NFATransitionsT

if TYPE_CHECKING:
    from absmt.automata.nfa import NFA


@dataclass
class SpotNFA:
    """Wrapper class for converting NFA components to Spot automaton."""

    states: set[NFAStateT]
    input_symbols: MSBFAlphabet
    transitions: NFATransitionsT
    initial_state: NFAStateT
    final_states: set[NFAStateT]
    _spot_automaton: Any = None  # spot.twa_graph | None
    _state_map: dict[NFAStateT, int] | None = None
    _ap_map: dict[MSBFAlphabetSymbol, Any] | None = None
    _bdict: Any = None  # spot.bdd_dict | None

    def __post_init__(self) -> None:
        """Initialize the Spot automaton after creation."""
        self._build_spot_automaton()

    def _build_spot_automaton(self) -> None:
        """Convert the custom NFA to a Spot automaton."""
        self._create_automaton()
        self._add_states()
        self._register_atomic_propositions()
        self._add_transitions()
        self._set_initial_state()
        self._set_acceptance_condition()

    def _create_automaton(self) -> None:
        """Create BDD dictionary and Spot automaton."""
        self._bdict = spot.make_bdd_dict()
        self._spot_automaton = spot.make_twa_graph(self._bdict)

    def _add_states(self) -> None:
        """Add states to the automaton."""
        self._state_map = {}
        state_list = list(self.states)

        if state_list:
            # Add required number of states
            self._spot_automaton.new_states(len(state_list))  # type: ignore[attr-defined]
            for i, state in enumerate(state_list):
                self._state_map[state] = i

    def _register_atomic_propositions(self) -> None:
        """Register atomic propositions and create BDD variables."""
        self._ap_map = {}
        for symbol in self.input_symbols.symbol_generator():
            symbol_str = str(symbol)
            ap_num = self._spot_automaton.register_ap(symbol_str)  # type: ignore[attr-defined]
            self._ap_map[symbol] = buddy.bdd_ithvar(ap_num)

    def _add_transitions(self) -> None:
        """Add transitions to the automaton."""
        if self._ap_map is None or self._state_map is None:
            return

        for src_state, transitions in self.transitions.items():
            for symbol, dst_states in transitions.items():
                cond = self._ap_map[symbol]
                for dst_state in dst_states:
                    self._spot_automaton.new_edge(  # type: ignore[attr-defined]
                        self._state_map[src_state], self._state_map[dst_state], cond
                    )

    def _set_initial_state(self) -> None:
        """Set the initial state of the automaton."""
        if self._state_map is not None and self.initial_state in self._state_map:
            initial_state_num = self._state_map[self.initial_state]
            self._spot_automaton.set_init_state(initial_state_num)  # type: ignore[attr-defined]

    def _set_acceptance_condition(self) -> None:
        """Set acceptance condition for Büchi automaton."""
        self._spot_automaton.set_acceptance(1, "Inf(0)")  # type: ignore[attr-defined]

        # For Büchi automata, mark states that should be visited
        # infinitely often
        if self._state_map is not None:
            for final_state in self.final_states:
                final_state_num = self._state_map[final_state]
                # Add a self-loop with true condition and acceptance mark
                self._spot_automaton.new_edge(  # type: ignore[attr-defined]
                    final_state_num, final_state_num, buddy.bddtrue, [0]
                )

    @property
    def spot_automaton(self) -> object:
        """Get the underlying Spot automaton."""
        if self._spot_automaton is None:
            self._build_spot_automaton()
        if self._spot_automaton is None:
            msg = "Failed to build Spot automaton"
            raise RuntimeError(msg)
        return self._spot_automaton

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
        return cls(
            states=nfa.states,
            input_symbols=nfa.input_symbols,
            transitions=nfa.transitions,
            initial_state=nfa.initial_state,
            final_states=nfa.final_states,
        )

    def __str__(self) -> str:
        """Return string representation showing the HOA format."""
        return self.to_hoa()
