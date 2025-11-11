import logging
from collections import deque
from dataclasses import InitVar, dataclass, field
from itertools import product
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
        """Check if the automaton's language is empty by performing BFS."""
        visited: list[bool] = [False] * self.twa_graph.num_states()
        queue = deque()

        initial_state = self.twa_graph.get_init_state_number()
        queue.append(initial_state)
        visited[initial_state] = True
        while queue:
            current_state = queue.popleft()
            if current_state in self._final_state_ids:
                return False

            for edge in self.twa_graph.out(current_state):
                next_state = edge.dst
                if not visited[next_state]:
                    visited[next_state] = True
                    queue.append(next_state)

        return True

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
            return True  # If no NFAs are provided, consider it trivially true

        if len(nfas) == 1:
            return not nfas[0].twa_graph.is_empty()

        automata_list: list[Any] = [nfa.twa_graph for nfa in nfas]

        # loop until the list has only two automata
        while len(automata_list) > 2:  # noqa: PLR2004
            next_level_automata: list[Any] = []
            for i in range(0, len(automata_list), 2):
                # If there is only one element left at the end of the list
                if i + 1 >= len(automata_list):
                    next_level_automata.append(automata_list[i])
                    break

                aut1 = automata_list[i]
                aut2 = automata_list[i + 1]
                logger.debug("Computing product of automata %d and %d", i, i + 1)
                product_aut = spot.product(aut1, aut2)
                logger.debug(
                    "Product computation finished for automata %d and %d", i, i + 1
                )

                # If the product automaton is empty, there is no common language
                if product_aut.is_empty():
                    return False

                next_level_automata.append(product_aut)

            # Update the list of automata for the next level
            automata_list = next_level_automata

        logger.debug("Computing final intersects for the last two automata")
        result = automata_list[0].intersects(automata_list[1])
        logger.debug("Final intersects computation finished")
        return result

    @staticmethod
    def intersect_all(*nfas: "SpotNFA") -> "SpotNFA":
        """Create a single automaton by taking the intersection of all given SpotNFA.

        Args:
            *nfas: SpotNFA instances to combine

        Returns:
            spot.twa_graph: The product automaton of all input automata

        """
        if not nfas:
            msg = "No NFAs provided for product."
            raise ValueError(msg)

        if len(nfas) == 1:
            return nfas[0].twa_graph

        automata_list: list[SpotNFA] = list(nfas)

        # 分割統治法のアイデア。
        # TODO: 作成途中で受理不能になったらそれ以降の計算を省略したい。
        while len(automata_list) > 1:
            next_level_automata = []
            for i in range(0, len(automata_list), 2):
                if i + 1 >= len(automata_list):
                    next_level_automata.append(automata_list[i])
                    break
                aut1 = automata_list[i]
                aut2 = automata_list[i + 1]
                product_aut = spot.product(aut1.twa_graph, aut2.twa_graph)

                # keep track on final states by id
                product_states: list[tuple[int, int]] = product_aut.get_product_states()
                mapping: dict[tuple[int, int], int] = {
                    state: idx for idx, state in enumerate(product_states)
                }
                product_aut_final_state_ids: set[int] = {
                    mapping[s]
                    for s in set(product(aut1.final_state_ids, aut2.final_state_ids))
                }

                next_level_automata.append(
                    SpotNFA.from_twa_graph(product_aut, product_aut_final_state_ids)
                )
            automata_list = next_level_automata

        # Return the merged automaton; note: final_state_ids[0] holds the
        # combined final-state tuples for the resulting product automaton.
        return automata_list[0]
