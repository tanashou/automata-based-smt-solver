from collections import defaultdict
from .presburger_arithmetic import PresburgerArithmetic
from .nfa import NFA
from .type import NFAStateT
from .utils import (
    make_binary_wildcard_strings,
    dot_product_with_wildcard,
)


# 1つのリテラルに対してnfaを作成していくクラス
class AutomataBuilder:
    INITIAL_STATE = "q0"

    def __init__(self, coefs: list[int], prb_arithmetic: PresburgerArithmetic, create_all: bool = False) -> None:
        self.coefs = coefs
        self.const = prb_arithmetic.const
        self.relation = prb_arithmetic.relation
        self.create_all = create_all  # for debug
        self.nfa = NFA(
            states={self.INITIAL_STATE, str(self.const)},
            input_symbols=make_binary_wildcard_strings(self.coefs),
            transitions=defaultdict(lambda: defaultdict(set)),
            initial_state=self.INITIAL_STATE,
            final_states=set([str(self.const)]),
        )
        self.work_list = [self.const]
        self.__build_completed = False

    @property
    def build_completed(self) -> bool:
        return self.__build_completed

    def next(self) -> bool:
        # TODO: self.relationによって、どの関数を呼び出すかを変えたい。relationクラスかenumを作成する
        return self.eq_to_nfa()

    """
    coefs: all the coefficients of the linear equations
    const: constant of the linear equation
    """

    def eq_to_nfa(self) -> bool:
        # when return False, the nfa is complete. No more works to do.
        partial_sat = False

        while self.work_list:
            current_state = self.work_list.pop()
            for symbol in self.nfa.input_symbols:
                dot = dot_product_with_wildcard(self.coefs, symbol)
                if (previous_state := 0.5 * (current_state - dot)).is_integer():
                    previous_state = int(previous_state)
                    if str(previous_state) not in self.nfa.states:
                        self.nfa.add_state(str(previous_state))
                        self.work_list.append(previous_state)
                    self.nfa.add_transition(str(previous_state), symbol, str(current_state))
                if current_state == -dot:
                    self.nfa.add_transition(self.INITIAL_STATE, symbol, str(current_state))
                    partial_sat = True
            if partial_sat:
                if not self.create_all:
                    return partial_sat

        # when the work_list is empty, building nfa is completed.
        self.__build_completed = True
        return partial_sat

    # def neq_to_nfa(a: list[int], c: int) -> None:
    #     pass

    def create_neq_nfa(self) -> None:
        # z_neq != 0 のnfaを作成する
        pass
