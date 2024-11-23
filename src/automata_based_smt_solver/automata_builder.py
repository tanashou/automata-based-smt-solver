from collections import defaultdict

from pysmt.fnode import FNode

from .nfa import NFA
from .utils import (
    dot_product_with_wildcard,
    make_binary_wildcard_strings,
)


# 1つのリテラルに対してnfaを作成していくクラス
class AutomataBuilder:
    INITIAL_STATE = "q0"

    def __init__(
        self,
        formula: FNode,
        declared_vars_index_map: dict[str, int],
        *,
        create_all: bool = False,
    ) -> None:
        # lhs, rhs は sympy.core や sympy.numbersとなる。
        # リンターはBasicとして認識するので無視する
        self.coefs: defaultdict[str, int] = defaultdict(
            int,
            {
                str(key): var
                for key, var in formula.lhs.as_coefficients_dict().items()  # type: ignore[attr-defined]
            },
        )
        # 同様に無視
        self.const: int = int(formula.rhs)  # type: ignore[attr-defined]
        # formula は Eq, Leq, Geq, Lt, Gt のみ。Eq が Relational を含むクラスなので無視
        self.relation: str = formula.rel_op  # type: ignore[attr-defined]
        self.declared_vars_index_map: dict[str, int] = declared_vars_index_map
        self.create_all: bool = create_all  # for debug
        self.nfa = NFA(
            states={self.INITIAL_STATE, str(self.const)},
            input_symbols=make_binary_wildcard_strings(
                declared_vars_index_map, self.coefs
            ),
            transitions=defaultdict(lambda: defaultdict(set), {}),
            initial_state=self.INITIAL_STATE,
            final_states={str(self.const)},
        )
        self.work_list = [self.const]
        self.__build_completed = False

    @property
    def build_completed(self) -> bool:
        return self.__build_completed

    def next(self) -> None:
        match self.relation:
            case "==":
                self.eq_to_nfa()
            case "<=":
                self.leq_to_nfa()

    def eq_to_nfa(self) -> None:
        partial_sat = False

        while self.work_list:
            current_state = self.work_list.pop()
            for symbol in self.nfa.input_symbols:
                dot = dot_product_with_wildcard(
                    self.declared_vars_index_map, self.coefs, symbol
                )
                if (current_state - dot) & 1 == 0:
                    previous_state = (current_state - dot) // 2
                    previous_state = int(previous_state)
                    if str(previous_state) not in self.nfa.states:
                        self.nfa.add_state(str(previous_state))
                        self.work_list.append(previous_state)
                    self.nfa.add_transition(
                        str(previous_state), symbol, str(current_state)
                    )
                if current_state == -dot:
                    self.nfa.add_transition(
                        self.INITIAL_STATE, symbol, str(current_state)
                    )
                    partial_sat = True
            # return after the for loop is finished.
            if partial_sat and not self.create_all:
                return

        # when the work_list is empty, building nfa is completed.
        self.__build_completed = True

    def leq_to_nfa(self) -> None:
        partial_sat = False

        while self.work_list:
            current_state = self.work_list.pop()
            for symbol in self.nfa.input_symbols:
                dot = dot_product_with_wildcard(
                    self.declared_vars_index_map, self.coefs, symbol
                )
                previous_state = (current_state - dot) // 2
                if str(previous_state) not in self.nfa.states:
                    self.nfa.add_state(str(previous_state))
                    self.work_list.append(previous_state)
                self.nfa.add_transition(str(previous_state), symbol, str(current_state))

                if current_state + dot >= 0:
                    self.nfa.add_transition(
                        self.INITIAL_STATE, symbol, str(current_state)
                    )
                    partial_sat = True
            # return after the for loop is finished.
            if partial_sat and not self.create_all:
                return

        # when the work_list is empty, building nfa is completed.
        self.__build_completed = True
