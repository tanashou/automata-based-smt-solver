from collections.abc import Generator
from itertools import product

from pysmt.fnode import FNode

from automata_based_smt_solver.automata.input_symbol import InputSymbol
from automata_based_smt_solver.automata.nfa import NFA
from automata_based_smt_solver.automata.state import INITIAL_STATE
from automata_based_smt_solver.build_status import BuildStatus
from automata_based_smt_solver.formula.type import FormulaData, FormulaType


# 1つのリテラルに対してnfaを作成していくクラス
class AutomataBuilder:
    def __init__(
        self,
        formula_data: FormulaData,
        all_vars: list[FNode],
        all_var_index_map: dict[FNode, int],
        *,
        create_all: bool = False,
    ) -> None:
        self.formula_data: FormulaData = formula_data
        self.create_all: bool = create_all  # for debug

        self.nfa = NFA()
        # initialize nfa
        self.nfa.add_state(self.formula_data.const)
        self.nfa.set_input_symbols(self._generate_input_symbols(all_vars))
        self.nfa.set_initial_state(INITIAL_STATE)
        self.nfa.add_final_state(self.formula_data.const)

        self.dots: dict[InputSymbol, int] = self._calc_dots(all_var_index_map)
        self.work_list = [self.formula_data.const]

        self._build_status = BuildStatus.UNTOUCHED

    @property
    def build_status(self) -> BuildStatus:
        return self._build_status

    # formula_data.vars と all_vars_index_map, all_vars を使う。
    def _generate_input_symbols(self, all_vars: list[FNode]) -> set[InputSymbol]:
        mask = "".join(
            "1" if var in self.formula_data.coeffs else "0" for var in all_vars
        )
        choices = [("0", "1") if ch == "1" else ("0",) for ch in mask]
        symbols = {"".join(bits) for bits in product(*choices)}
        return {InputSymbol(symbol, mask) for symbol in symbols}

    def _calc_dots(self, all_var_index_map: dict[FNode, int]) -> dict[InputSymbol, int]:
        result = {}
        var_coef_index_pairs = [
            (coeff, all_var_index_map[var])
            for var, coeff in self.formula_data.coeffs.items()
        ]
        for symbol in self.nfa.input_symbols:
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
            self._build_status = BuildStatus.ONGOING
            next(self._build_gen)
        except StopIteration:
            self._build_status = BuildStatus.COMPLETED
        return self._build_status

    def eq_to_nfa(self) -> Generator[None]:
        partial_sat = False

        while self.work_list:
            current_state_val = self.work_list.pop()
            for symbol in self.nfa.input_symbols:
                dot = self.dots[symbol]
                if (current_state_val - dot) & 1 == 0:
                    previous_state_val = (current_state_val - dot) // 2
                    if not self.nfa.contains_state(previous_state_val):
                        self.nfa.add_state(previous_state_val)
                        self.work_list.append(previous_state_val)
                    self.nfa.add_transition(
                        previous_state_val, symbol, current_state_val
                    )
                if current_state_val == -dot:
                    self.nfa.add_transition(INITIAL_STATE, symbol, current_state_val)
                    partial_sat = True

            if partial_sat and not self.create_all:
                yield

    def le_to_nfa(self) -> Generator[None]:
        partial_sat = False

        while self.work_list:
            current_state_val = self.work_list.pop()
            for symbol in self.nfa.input_symbols:
                dot = self.dots[symbol]
                previous_state_val = (current_state_val - dot) // 2
                if not self.nfa.contains_state(previous_state_val):
                    self.nfa.add_state(previous_state_val)
                    self.work_list.append(previous_state_val)
                self.nfa.add_transition(previous_state_val, symbol, current_state_val)

                if current_state_val + dot >= 0:
                    self.nfa.add_transition(INITIAL_STATE, symbol, current_state_val)
                    partial_sat = True
            if partial_sat and not self.create_all:
                yield

    def false_to_nfa(self) -> Generator[None]:
        final_state = self.formula_data.const
        for symbol in self.nfa.input_symbols:
            dot_value = self.dots[symbol]
            if dot_value == 1:
                self.nfa.add_transition(INITIAL_STATE, symbol, final_state)
                yield
                break

    def true_to_nfa(self) -> Generator[None]:
        final_state = self.formula_data.const
        for symbol in self.nfa.input_symbols:
            dot_value = self.dots[symbol]
            if dot_value == 0:
                self.nfa.add_transition(INITIAL_STATE, symbol, final_state)
                yield
                break
