import itertools
from collections import defaultdict
from src.my_automata.mutable_nfa import MutableNFA as NFA
from src.my_automata.type import SymbolT, NFAStateT, NFAPathT, NFATransitionT
from src.my_automata.utils import (
    make_binary_wildcard_strings,
    dot_product_with_wildcard,
    apply_mask,
    intersection_containing_wildcard,
)


# 1つのリテラルに対してnfaを作成していくクラス
class AutomataBuilder:
    INITIAL_STATE = "q0"

    def __init__(self, coefs: list[int], const: int, relation: str, create_all: bool = False) -> None:
        self.coefs = coefs
        self.const = const
        self.relation = relation
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

        # when the work_list is empty, the nfa is complete.
        self.__build_completed = True
        return partial_sat

    # def neq_to_nfa(a: list[int], c: int) -> None:
    #     pass


# TODO: タプルのネストを外す。tuple(itertools.chain.from_iterable(tuple))でいける
def nfa_intersection(nfa1: NFA, nfa2: NFA) -> NFA:
    initial_state = (nfa1.initial_state, nfa2.initial_state)
    nfa = NFA(
        states=set(),
        input_symbols=intersection_containing_wildcard(nfa1.input_symbols, nfa2.input_symbols),
        transitions=defaultdict(lambda: defaultdict(set)),
        initial_state=initial_state,
        final_states=set(),
    )
    work_list: list[NFAStateT] = [initial_state]

    if not nfa.input_symbols:
        raise ValueError("The given NFAs have no common input symbols")

    # create a mask for each nfa. The mask is used to apply wildcard to the input symbol
    mask1: list[bool] = [char != "*" for char in list(nfa1.input_symbols)[0]]
    mask2: list[bool] = [char != "*" for char in list(nfa2.input_symbols)[0]]

    while work_list:
        current_state1, current_state2 = work_list.pop()
        nfa.add_state((current_state1, current_state2))
        if current_state1 in nfa1.final_states and current_state2 in nfa2.final_states:
            nfa.add_final_state((current_state1, current_state2))
        for symbol in nfa.input_symbols:
            next_states1 = nfa1.get_next_states(current_state1, apply_mask(symbol, mask1))
            next_states2 = nfa2.get_next_states(current_state2, apply_mask(symbol, mask2))
            for next_state1, next_state2 in set(itertools.product(next_states1, next_states2)):
                nfa.add_transition((current_state1, current_state2), symbol, (next_state1, next_state2))
                if (next_state1, next_state2) not in nfa.states:
                    work_list.append((next_state1, next_state2))

    return nfa
