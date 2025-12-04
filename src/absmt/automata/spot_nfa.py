# ruff: noqa: T201
import logging
from dataclasses import InitVar, dataclass, field
from typing import Any

import buddy
import spot

from absmt.automata.msbf_alphabet import MSBFAlphabet
from absmt.automata.msbf_alphabet_symbol import MSBFAlphabetSymbol
from absmt.automata.nfa import NFA, NFAStateT, NFATransitionsT
from absmt.formula.type import FormulaData

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

    formula_data: FormulaData | None = field(default=None, init=False)

    def __post_init__(self, nfa: NFA, bdd_dict: Any) -> None:  # noqa: ANN401
        """Initialize the Spot automaton after creation."""
        self._create_automaton(bdd_dict)
        self._register_ap(nfa.alphabet)
        self._add_states(nfa.states)
        self._set_initial_state(nfa.initial_state)
        self._add_transitions(nfa.transitions, nfa.final_states, nfa.alphabet)

    def set_formula_data(self, formula_data: FormulaData) -> None:
        self.formula_data = formula_data

    def get_registered_ap(self) -> set[str]:
        """Get the list of registered atomic propositions."""
        return {str(ap) for ap in self.twa_graph.ap()}

    def custom_print(self) -> None:
        bdict = self.twa_graph.get_dict()
        print("Acceptance:", self.twa_graph.get_acceptance())
        print("Number of sets:", self.twa_graph.num_sets())
        print("Number of states: ", self.twa_graph.num_states())
        print("Initial states: ", self.twa_graph.get_init_state_number())
        print("Atomic propositions:", end="")
        for ap in self.twa_graph.ap():
            print(" ", ap, " (=", bdict.varnum(ap), ")", sep="", end="")
        print()
        # Templated methods are not available in Python, so we cannot
        # retrieve/attach arbitrary objects from/to the automaton.  However the
        # Python bindings have get_name() and set_name() to access the
        # "automaton-name" property.
        name = self.twa_graph.get_name()
        if name:
            print("Name: ", name)
        print(
            "Deterministic:",
            self.twa_graph.prop_universal() and self.twa_graph.is_existential(),
        )
        print("Unambiguous:", self.twa_graph.prop_unambiguous())
        print("State-Based Acc:", self.twa_graph.prop_state_acc())
        print("Terminal:", self.twa_graph.prop_terminal())
        print("Weak:", self.twa_graph.prop_weak())
        print("Inherently Weak:", self.twa_graph.prop_inherently_weak())
        print("Stutter Invariant:", self.twa_graph.prop_stutter_invariant())
        for s in range(self.twa_graph.num_states()):
            print(f"State {s}:")
            for t in self.twa_graph.out(s):
                print(f"  edge({t.src} -> {t.dst})")
                # bdd_print_formula() is designed to print on a std::ostream, and
                # is inconvenient to use in Python.  Instead we use
                # bdd_format_formula() as this simply returns a string.
                print("    label =", spot.bdd_format_formula(bdict, t.cond))
                print("    acc sets =", t.acc)

    @classmethod
    def from_twa_graph(
        cls,
        twa_graph: Any,  # noqa: ANN401
        formula_data: FormulaData | None = None,
    ) -> "SpotNFA":
        """Create SpotNFA from an existing TWA graph."""
        obj = cls.__new__(cls)
        obj.twa_graph = twa_graph
        obj._state_map = {}  # noqa: SLF001
        obj.formula_data = formula_data
        return obj

    def _create_automaton(self, bdd_dict: Any) -> None:  # noqa: ANN401
        """Create BDD dictionary and Spot automaton."""
        self.twa_graph = spot.make_twa_graph(bdd_dict)
        self.twa_graph.set_buchi()
        # Pretend this is state-based acceptance
        # 終端変数を登録
        self._end_var = self.twa_graph.register_ap("_END")

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

        not_end_bdd = -buddy.bdd_ithvar(self._end_var)
        end_bdd = buddy.bdd_ithvar(self._end_var)

        for start_state, trans in transitions.items():
            start_state_id = self._state_map[start_state]

            # 受理状態からの遷移全てを受理条件に追加
            for symbol, end_states in trans.items():
                for end_state in end_states:
                    end_state_id = self._state_map[end_state]
                    formula = self._symbol_to_formula(all_vars, symbol) & not_end_bdd
                    self.twa_graph.new_edge(start_state_id, end_state_id, formula)

        sink_state_id = self.twa_graph.new_state()
        # 受理状態からシンク状態への遷移を追加
        for state in final_states:
            state_id = self._state_map[state]
            self.twa_graph.new_edge(state_id, sink_state_id, end_bdd)

        # シンク状態に自己ループを追加。受理条件付き。
        self.twa_graph.new_edge(
            sink_state_id, sink_state_id, buddy.bddtrue, [acceptance_set]
        )

        self.twa_graph.merge_edges()

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
        return self.twa_graph.is_empty()

    def num_states(self) -> int:
        """Get the number of states in the automaton."""
        return self.twa_graph.num_states()

    def minimize(self, automata_type: int) -> None:
        """Minimize the automaton using Spot's minimization."""
        # automata_type: spot.postprocessor.<Type>

        self.twa_graph = spot.complete(self.twa_graph)
        post = spot.postprocessor()
        # High だとものによって適用されるアルゴリズムが変わる。全部統一させたい。
        post.set_level(spot.postprocessor.Medium)
        # 状態数を小さくすることを優先
        post.set_pref(spot.postprocessor.Small)
        # Weakオートマトンは最小の決定性Büchiオートマトンになる
        post.set_pref(spot.postprocessor.Deterministic)
        post.set_type(automata_type)
        minimized_aut = post.run(self.twa_graph)
        self.twa_graph = minimized_aut

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
        result = SpotNFA.from_twa_graph(product_aut)

        # Early return if the result is empty
        if result.is_empty():
            # Record empty result as -1
            if state_counts is not None:
                structure_str = str(structure)
                state_counts[structure_str] = -1
            return None

        result.minimize(spot.postprocessor.GeneralizedBuchi)

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

    @staticmethod
    def union_all(*nfas: "SpotNFA") -> "SpotNFA":
        """Create a single automaton by taking the union of all given SpotNFA.

        Args:
            *nfas: SpotNFA instances to combine

        Returns:
            SpotNFA: The union automaton of all input automata

        """
        if not nfas:
            msg = "No NFAs provided for union."
            raise ValueError(msg)

        if len(nfas) == 1:
            return nfas[0]

        automata_list = list(nfas)

        result_aut = automata_list[0].twa_graph

        for aut in automata_list[1:]:
            result_aut = spot.product_or(result_aut, aut.twa_graph)

        result = SpotNFA.from_twa_graph(result_aut)
        result.minimize(spot.postprocessor.GeneralizedBuchi)

        return result

    @staticmethod
    def complement(nfa: "SpotNFA") -> "SpotNFA":
        """Create a complement automaton from the nfa."""
        # 1. 通常の補集合計算
        comp_graph = spot.complement(nfa.twa_graph)

        # 2. "Strict Universe" (非空の宇宙) オートマトンの作成
        # 構造: Init -(!_END)-> q_wait -(!_END)*-> q_wait -(_END)-> q_sink

        universe = spot.make_twa_graph(nfa.twa_graph.get_dict())
        universe.set_buchi()

        q_init = universe.new_state()  # 初期状態
        q_wait = universe.new_state()  # 2ビット目以降の待機
        q_sink = universe.new_state()  # 受理シンク

        universe.set_init_state(q_init)

        # 変数IDの取得
        end_ap = universe.register_ap("_END")
        end_bdd = buddy.bdd_ithvar(end_ap)
        not_end_bdd = buddy.bdd_not(end_bdd)

        # -- 遷移の構築 --

        # 1. 初期状態からは、必ず !_END (ビット) を読まなければならない
        #    いきなり _END が来ると遷移先がないため脱落する
        universe.new_edge(q_init, q_wait, not_end_bdd)

        # 2. q_wait: その後は !_END が続く限りループ、_END が来たら受理
        universe.new_edge(q_wait, q_wait, not_end_bdd)
        universe.new_edge(q_wait, q_sink, end_bdd)

        # 3. q_sink: 受理ループ
        universe.new_edge(q_sink, q_sink, buddy.bddtrue, [0])

        # 3. 積集合をとる
        result_graph = spot.product(comp_graph, universe)

        result = SpotNFA.from_twa_graph(result_graph)
        result.minimize(spot.postprocessor.Buchi)

        return result

    @staticmethod
    def projection(nfa: "SpotNFA", quantified_vars: list[str]) -> "SpotNFA":
        """Remove the given ap from all transition guards in the automaton.

        Args:
            nfa (SpotNFA): The automaton from which atomic propositions will be removed.
            quantified_vars (list[str]):
                List of atomic proposition names to remove (e.g., ["x", "y"]).

        """
        # 1. 新しいオートマトンのガワを作成(辞書は共有)
        old_g = nfa.twa_graph
        new_g = spot.make_twa_graph(old_g.get_dict())

        # 2. 受理条件と状態数をコピー
        # set_buchi() ではなく元の受理条件を引き継ぐ
        new_g.copy_acceptance_of(old_g)
        new_g.new_states(old_g.num_states())
        new_g.set_init_state(old_g.get_init_state_number())

        # 3. 消去する変数の特定と、残す変数の登録
        vars_to_remove = set(quantified_vars)

        # (A) 残す変数を新しいオートマトンに登録する
        for ap in old_g.ap():
            ap_name = ap.ap_name()
            if ap_name not in vars_to_remove:
                new_g.register_ap(ap_name)

        # (B) 消去するためのBDD Cube(連言)を作成
        cube = buddy.bddtrue
        for name in quantified_vars:
            # register_ap は既存のAPならそのIDを返すので、IDルックアップとして使える
            var_id = old_g.register_ap(name)
            cube = buddy.bdd_and(cube, buddy.bdd_ithvar(var_id))

        # 4. 全遷移を走査し、条件から変数を存在量化(射影)してコピー
        for s in range(old_g.num_states()):
            for edge in old_g.out(s):
                # cond 内の cube に含まれる変数を消去
                new_cond = buddy.bdd_exist(edge.cond, cube)
                new_g.new_edge(s, edge.dst, new_cond, edge.acc)

        result = SpotNFA.from_twa_graph(new_g)
        result.minimize(spot.postprocessor.Buchi)

        return result
