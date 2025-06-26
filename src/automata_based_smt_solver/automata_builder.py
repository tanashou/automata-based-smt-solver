from collections import defaultdict
from collections.abc import Generator

from pysmt.fnode import FNode

from automata_based_smt_solver.automata.msbf_alphabet import MSBFAlphabet
from automata_based_smt_solver.automata.msbf_alphabet_symbol import MSBFAlphabetSymbol
from automata_based_smt_solver.automata.nfa import NFA
from automata_based_smt_solver.build_status import BuildStatus
from automata_based_smt_solver.formula.type import FormulaData, FormulaType


# 1つのリテラルに対してnfaを作成していくクラス
class AutomataBuilder:
    def __init__(
        self,
        formula_data: FormulaData,
        all_vars: list[FNode],
        all_var_index_map: dict[FNode, int],
        used_vars: list[FNode],
        *,
        create_all: bool = False,
    ) -> None:
        self.formula_data: FormulaData = formula_data
        self.create_all: bool = create_all  # for debug

        initial_state = "q0"

        self.nfa = NFA(
            states={initial_state},
            initial_state=initial_state,
            input_symbols=MSBFAlphabet(all_vars, used_vars),
            transitions=defaultdict(lambda: defaultdict(set)),
            final_states={self.formula_data.const},
        )

        self.dots: dict[MSBFAlphabetSymbol, int] = self._calc_dots(all_var_index_map)
        self.work_list = [self.formula_data.const]

        self._build_status = BuildStatus.UNTOUCHED

    @property
    def build_status(self) -> BuildStatus:
        return self._build_status

    def _calc_dots(
        self, all_var_index_map: dict[FNode, int]
    ) -> dict[MSBFAlphabetSymbol, int]:
        result = {}
        var_coef_index_pairs = [
            (coeff, all_var_index_map[var])
            for var, coeff in self.formula_data.coeffs.items()
        ]
        for symbol in self.nfa.input_symbols.symbol_generator():
            result[symbol] = symbol.dot(var_coef_index_pairs)
        return result

    def _build_nfa_generator(self) -> Generator[None]:
        # yield を使って 各種nfa変換関数を呼び出す
        match self.formula_data.formula_type:
            case FormulaType.EQ:
                yield from self.eq_to_nfa()
            case FormulaType.LE:
                yield from self.le_to_nfa()
            case FormulaType.BOOL:
                if self.formula_data.has_negation_before_bool_var:
                    yield from self.false_to_nfa()
                else:
                    yield from self.true_to_nfa()

    def build_step(self) -> BuildStatus:
        if not hasattr(self, "_build_gen"):
            self._build_gen = self._build_nfa_generator()
        try:
            next(self._build_gen)
            self._build_status = BuildStatus.ONGOING
        except StopIteration:
            self._build_status = BuildStatus.COMPLETED
        return self._build_status

    def eq_to_nfa(self) -> Generator[None]:
        partial_sat = False

        while self.work_list:
            current_state = self.work_list.pop()
            for symbol in self.nfa.input_symbols.symbol_generator():
                dot = self.dots[symbol]
                if (current_state - dot) & 1 == 0:
                    previous_state = (current_state - dot) // 2
                    if previous_state not in self.nfa.states:
                        self.nfa.add_state(previous_state)
                        self.work_list.append(previous_state)
                    self.nfa.add_transition(previous_state, symbol, current_state)
                if current_state == -dot:
                    self.nfa.add_transition(
                        self.nfa.initial_state, symbol, current_state
                    )
                    partial_sat = True

            if partial_sat and not self.create_all:
                yield

    def le_to_nfa(self) -> Generator[None]:
        partial_sat = False

        while self.work_list:
            current_state = self.work_list.pop()
            for symbol in self.nfa.input_symbols.symbol_generator():
                dot = self.dots[symbol]
                previous_state = (current_state - dot) // 2
                if previous_state not in self.nfa.states:
                    self.nfa.add_state(previous_state)
                    self.work_list.append(previous_state)
                self.nfa.add_transition(previous_state, symbol, current_state)

                if current_state + dot >= 0:
                    self.nfa.add_transition(
                        self.nfa.initial_state, symbol, current_state
                    )
                    partial_sat = True
            if partial_sat and not self.create_all:
                yield

    def false_to_nfa(self) -> Generator[None]:
        # add dead state
        dead_state = -1
        self.nfa.add_state(dead_state)
        # add final state
        final_state = self.formula_data.const
        self.nfa.add_state(final_state)

        # length of input_symbols is always 2 for boolean formulas
        for symbol in self.nfa.input_symbols.symbol_generator():
            dot_value = self.dots[symbol]
            if dot_value == 1:
                self.nfa.add_transition(self.nfa.initial_state, symbol, final_state)
            else:
                self.nfa.add_transition(self.nfa.initial_state, symbol, dead_state)

            # add loop to dead state and final state
            self.nfa.add_transition(final_state, symbol, final_state)
            self.nfa.add_transition(dead_state, symbol, dead_state)
        yield

    def true_to_nfa(self) -> Generator[None]:
        # add dead state
        dead_state = -1
        self.nfa.add_state(dead_state)
        # add final state
        final_state = self.formula_data.const
        self.nfa.add_state(final_state)

        # length of input_symbols is always 2 for boolean formulas
        for symbol in self.nfa.input_symbols.symbol_generator():
            dot_value = self.dots[symbol]
            if dot_value == 0:
                self.nfa.add_transition(self.nfa.initial_state, symbol, final_state)
            else:
                self.nfa.add_transition(self.nfa.initial_state, symbol, dead_state)

            # add loop to dead state and final state
            self.nfa.add_transition(final_state, symbol, final_state)
            self.nfa.add_transition(dead_state, symbol, dead_state)
        yield
