import logging
from dataclasses import InitVar, dataclass, field
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
    _bdd_var_str_to_id: dict[str, Any] = field(default_factory=dict, init=False)

    def __post_init__(self, nfa: NFA, bdd_dict: Any) -> None:  # noqa: ANN401
        """Initialize the Spot automaton after creation."""
        self._create_automaton(bdd_dict)
        self._register_ap(nfa.alphabet)
        self._add_states(nfa.states)
        self._set_initial_state(nfa.initial_state)
        self._add_transitions(nfa.transitions, nfa.final_states, nfa.alphabet)

    def _create_automaton(self, bdd_dict: Any) -> None:  # noqa: ANN401
        """Create BDD dictionary and Spot automaton."""
        self.twa_graph = spot.make_twa_graph(bdd_dict)
        self.twa_graph.set_buchi()
        # Pretend this is state-based acceptance
        self.twa_graph.prop_state_acc(True)  # noqa: FBT003

    def _register_ap(self, alphabet: MSBFAlphabet) -> None:
        """Register atomic propositions for each variable in the BDD."""
        for var in alphabet.used_vars:
            bdd_var_id = self.twa_graph.register_ap(var)
            self._bdd_var_str_to_id[var] = bdd_var_id

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

        for state_from, trans in transitions.items():
            state_from_id = self._state_map[state_from]
            is_state_from_final = state_from in final_states

            # 受理状態からの遷移全てを受理条件に追加
            for symbol, state_to_set in trans.items():
                for state_to in state_to_set:
                    state_to_id = self._state_map[state_to]

                    formula = self._symbol_to_formula(all_vars, symbol)

                    # Buchiオートマトンに変換するため受理状態からの遷移を受理条件に追加
                    if is_state_from_final:
                        self.twa_graph.new_edge(
                            state_from_id, state_to_id, formula, [0]
                        )
                    else:
                        self.twa_graph.new_edge(state_from_id, state_to_id, formula)

        # Buchiオートマトンに変換するため、無限語を受理できるようにする
        for final_state in final_states:
            if transitions.get(final_state) is None:
                # If there are no transitions from the final state, create a self-loop
                final_state_id = self._state_map[final_state]
                self.twa_graph.new_edge(
                    final_state_id,
                    final_state_id,
                    buddy.bddtrue,
                )

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
        return self.twa_graph.to_str("hoa")

    def to_dot(self) -> str:
        """Convert the automaton to DOT format string."""
        return self.twa_graph.to_str("dot")

    def accepts(self, word: str) -> bool:
        """Check if the automaton accepts a given word."""
        msg = "Word acceptance checking not yet implemented"
        raise NotImplementedError(msg)

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
    def product_all(*nfas: "SpotNFA") -> "SpotNFA":
        """Create a single automaton by taking the product of all given SpotNFA.

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

        automata_list = [nfa.twa_graph for nfa in nfas]

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
                product_aut = spot.product(aut1, aut2)
                next_level_automata.append(product_aut)
            automata_list = next_level_automata

        return automata_list[0]

    def projection(self, quantified_vars: list[str]) -> None:
        """Remove the given ap from all transition guards in the automaton.

        Args:
            quantified_vars (list[str]):
                List of atomic proposition names to remove (e.g., ["x", "y"]).

        Note:
            Since all guards are conjunctions, applying buddy.bdd_exist
            eliminates the quantified variables.
            spot_aut does not allow modifying the guards directly,
            so we create a new automaton with the modified guards.

        """
        new_twa = spot.make_twa_graph(self.twa_graph.get_dict())
        new_twa.set_buchi()
        new_twa.prop_state_acc(True)  # noqa: FBT003
        new_twa.new_states(self.twa_graph.num_states())
        new_twa.set_init_state(self.twa_graph.get_init_state_number())

        # Build a cube (conjunction) of all variables to eliminate
        # Using bddtrue() as neutral element for conjunction
        cube = buddy.bddtrue
        for name in quantified_vars:
            varid = self._bdd_var_str_to_id[name]
            cube = buddy.bdd_and(cube, buddy.bdd_ithvar(varid))

        # Iterate over all edges and replace their guard with the quantified guard
        for state in range(self.twa_graph.num_states()):
            for edge in self.twa_graph.out(state):
                old_guard = edge.cond()  # BDD of the transition condition
                new_guard = buddy.bdd_exist(old_guard, cube)  # ∃(ap_names). old_guard
                new_twa.new_edge(state, edge.dst(), new_guard, edge.acc())

        # If you plan to reuse the automaton, you may want to simplify/cleanup:
        # aut.merge_states() or spot.postprocess functions as appropriate
        self.twa_graph.merge_states()
        self.twa_graph = new_twa
