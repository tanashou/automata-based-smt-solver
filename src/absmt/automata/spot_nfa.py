import logging
from dataclasses import InitVar, dataclass, field
from itertools import product
from typing import Any

import buddy
import spot

from absmt.automata.msbf_alphabet import MSBFAlphabet
from absmt.automata.msbf_alphabet_symbol import MSBFAlphabetSymbol
from absmt.automata.nfa import NFA, NFAStateT, NFATransitionsT

logger = logging.getLogger(__name__)

# Tournament structure type: int for leaf (automaton index), tuple for internal node
TournamentStructure = int | tuple["TournamentStructure", "TournamentStructure"]


@dataclass
class SpotNFA:
    """Wrapper class for converting NFA components to Spot automaton."""

    nfa: InitVar[NFA]
    # must use the same bdd_dict instance for all SpotNFA instances
    # when applying functions like spot.product
    bdd_dict: InitVar[Any]  # spot.bdd_dict

    # twa: transition-based ω automata
    twa_graph: Any = field(init=False)  # spot.twa_graph
    _state_map: dict[NFAStateT, int] = field(default_factory=dict, init=False)

    def __post_init__(self, nfa: NFA, bdd_dict: Any) -> None:  # noqa: ANN401
        """Initialize the Spot automaton after creation."""
        self._create_automaton(bdd_dict)
        self._register_ap(nfa.alphabet)
        self._add_states(nfa.states)
        self._set_initial_state(nfa.initial_state)
        self._add_transitions(nfa.transitions, nfa.final_states, nfa.alphabet)

        self._final_state_ids: set[int] = {
            self._state_map[state] for state in nfa.final_states
        }

    @property
    def final_state_ids(self) -> set[int]:
        """Get the set of final state IDs."""
        return self._final_state_ids

    @classmethod
    def from_twa_graph(
        cls,
        twa_graph: Any,  # noqa: ANN401
        final_state_ids: set[int],
    ) -> "SpotNFA":
        """Create SpotNFA from an existing TWA graph."""
        obj = cls.__new__(cls)
        obj.twa_graph = twa_graph
        obj._state_map = {}  # noqa: SLF001
        obj._final_state_ids = final_state_ids  # noqa: SLF001
        return obj

    def _create_automaton(self, bdd_dict: Any) -> None:  # noqa: ANN401
        """Create BDD dictionary and Spot automaton."""
        self.twa_graph = spot.make_twa_graph(bdd_dict)
        self.twa_graph.set_buchi()
        # Pretend this is state-based acceptance
        self.twa_graph.prop_state_acc(True)  # noqa: FBT003

    def _register_ap(self, alphabet: MSBFAlphabet) -> None:
        """Register atomic propositions for each variable in the BDD."""
        for var in alphabet.used_vars:
            self.twa_graph.register_ap(var)

    def _add_states(self, states: set[NFAStateT]) -> None:
        """Add states to the automaton."""
        self._state_map = {}

        if states:
            # Add required number of states
            self.twa_graph.new_states(len(states))
            # spot.aut の状態と NFA の状態を対応させるためのマップを作成
            for i, state in enumerate(states):
                self._state_map[state] = i

    def _set_initial_state(self, initial_state: NFAStateT) -> None:
        """Set the initial state of the automaton."""
        if self._state_map is not None and initial_state in self._state_map:
            initial_state_id = self._state_map[initial_state]
            self.twa_graph.set_init_state(initial_state_id)

    def _add_transitions(
        self,
        transitions: NFATransitionsT,
        final_states: set[NFAStateT],
        alphabet: MSBFAlphabet,
    ) -> None:
        """Add transitions to the automaton."""
        # Cache alphabet information to avoid repeated access
        all_vars = alphabet.all_vars
        acceptance_set = 0

        for start_state, trans in transitions.items():
            start_state_id = self._state_map[start_state]
            is_state_from_final = start_state in final_states

            # 受理状態からの遷移全てを受理条件に追加
            for symbol, end_states in trans.items():
                for end_state in end_states:
                    end_state_id = self._state_map[end_state]
                    formula = self._symbol_to_formula(all_vars, symbol)

                    # Buchiオートマトンに変換するため受理状態からの遷移を受理条件に追加
                    if is_state_from_final:
                        self.twa_graph.new_edge(
                            start_state_id, end_state_id, formula, [acceptance_set]
                        )
                    else:
                        self.twa_graph.new_edge(start_state_id, end_state_id, formula)

        self.twa_graph.merge_edges()
        self.twa_graph.merge_states()

    def _symbol_to_formula(
        self, all_vars: list[str], symbol: MSBFAlphabetSymbol
    ) -> object:
        """Optimized version that avoids repeated alphabet access."""
        # Start with True (bddtrue)
        result = buddy.bddtrue

        symbol_str = str(symbol)
        for i, bit in enumerate(symbol_str):
            var_name = str(all_vars[i])

            if bit == "1":
                bdd_var_id = self.twa_graph.register_ap(var_name)
                # Bit is 1 means variable is True
                result = result & buddy.bdd_ithvar(bdd_var_id)
            elif bit == "0":
                bdd_var_id = self.twa_graph.register_ap(var_name)
                # Bit is 0 means variable is False (negated)
                result = result & (-buddy.bdd_ithvar(bdd_var_id))
            # Skip wildcards

        return result

    def to_hoa(self) -> str:
        """Convert the automaton to HOA format string."""
        return self.twa_graph.to_str("hoa")

    def to_dot(self) -> str:
        """Convert the automaton to DOT format string."""
        return self.twa_graph.to_str("dot")

    def show(self, style: str = "v") -> None:
        """Show the automaton using spot's visualizer (for debugging).

        The `name` argument is forwarded to the underlying `twa_graph.show()`
        call. This method intentionally swallows exceptions and logs them so
        debug-printing won't break normal execution.
        """
        try:
            try:
                # spot.jupyter.display_inline renders automata inside notebooks
                from spot.jupyter import display_inline  # noqa: PLC0415

                display_inline(self.twa_graph)

            except ImportError:
                # Not in a Jupyter environment or display_inline not available.
                logger.exception("Failed to import spot.jupyter.display_inline")

            self.twa_graph.show(style)
        except Exception:
            logger.exception(
                "Failed to show Spot automaton; fallback to HOA/DOT available"
            )

    def accepts(self, word: str) -> bool:
        """Check if the automaton accepts a given word."""
        msg = "Word acceptance checking not yet implemented"
        raise NotImplementedError(msg)

    def __str__(self) -> str:
        """Return string representation showing the HOA format."""
        return self.to_hoa()

    def is_empty(self) -> bool:
        # spot.product は到達可能な状態だけ構築するため、この方法で十分。
        return bool(not self.final_state_ids)

    def num_states(self) -> int:
        """Get the number of states in the automaton."""
        return self.twa_graph.num_states()

    @staticmethod
    def _generate_default_structure(n: int) -> TournamentStructure:
        """Generate a default left-to-right balanced tournament structure.

        Args:
            n: Number of automata

        Returns:
            TournamentStructure: A balanced binary tree structure

        """
        if n == 1:
            return 0

        # Create a balanced binary tree by dividing in half
        mid = n // 2
        left = 0 if mid == 1 else SpotNFA._generate_default_structure(mid)

        # Adjust indices for the right subtree
        def shift_indices(
            structure: TournamentStructure, offset: int
        ) -> TournamentStructure:
            if isinstance(structure, int):
                return structure + offset
            return (
                shift_indices(structure[0], offset),
                shift_indices(structure[1], offset),
            )

        right = (
            mid
            if n - mid == 1
            else shift_indices(SpotNFA._generate_default_structure(n - mid), mid)
        )

        return (left, right)

    @staticmethod
    def intersect_by_structure(
        nfas: list["SpotNFA"],
        structure: TournamentStructure,
        state_counts: dict[str, int] | None = None,
    ) -> "SpotNFA | None":
        """Execute intersection following a specific tournament structure.

        Args:
            nfas: List of automata to intersect
            structure: Tournament structure specifying the order of intersections
            state_counts: Optional dict to record state counts for each
                intermediate result

        Returns:
            SpotNFA | None: The result of the intersection, or None if the
                intersection is empty

        """
        if isinstance(structure, int):
            # Leaf node: return the automaton at the specified index
            return nfas[structure]

        # Internal node: recursively intersect left and right
        left_result = SpotNFA.intersect_by_structure(nfas, structure[0], state_counts)
        right_result = SpotNFA.intersect_by_structure(nfas, structure[1], state_counts)

        # Early return if either side is empty
        if left_result is None or right_result is None:
            # Record empty result as -1
            if state_counts is not None:
                structure_str = str(structure)
                state_counts[structure_str] = -1
            return None

        # Perform binary intersection
        product_aut = spot.product(left_result.twa_graph, right_result.twa_graph)
        product_states: list[tuple[int, int]] = product_aut.get_product_states()
        mapping: dict[tuple[int, int], int] = {
            state: idx for idx, state in enumerate(product_states)
        }

        product_aut_final_state_ids: set[int] = {
            mapping[state]
            for state in product(
                left_result.final_state_ids, right_result.final_state_ids
            )
            if state in mapping
        }

        result = SpotNFA.from_twa_graph(product_aut, product_aut_final_state_ids)

        # Early return if the result is empty
        if result.is_empty():
            # Record empty result as -1
            if state_counts is not None:
                structure_str = str(structure)
                state_counts[structure_str] = -1
            return None

        # Record state count if dict is provided
        if state_counts is not None:
            structure_str = str(structure)
            state_counts[structure_str] = result.num_states()

        return result

    @staticmethod
    def intersect_all(
        *nfas: "SpotNFA",
        tournament_structure: TournamentStructure | None = None,
        state_counts: dict[str, int] | None = None,
    ) -> "SpotNFA | None":
        """Create a single automaton by taking the intersection of all given SpotNFA.

        Args:
            *nfas: SpotNFA instances to combine
            tournament_structure: Optional tournament structure specifying the order
                of intersections. If None, generates a default balanced structure.
            state_counts: Optional dict to record state counts for each
                intermediate result

        Returns:
            SpotNFA | None: The product automaton of all input automata, or None
                if the intersection is empty

        """
        if not nfas:
            msg = "No NFAs provided for product."
            raise ValueError(msg)

        if len(nfas) == 1:
            return nfas[0]

        automata_list = list(nfas)

        # Generate default structure if not provided
        if tournament_structure is None:
            tournament_structure = SpotNFA._generate_default_structure(
                len(automata_list)
            )

        return SpotNFA.intersect_by_structure(
            automata_list, tournament_structure, state_counts
        )
