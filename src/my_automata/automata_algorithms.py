import itertools
from collections import defaultdict
from my_automata.mutable_nfa import MutableNFA as NFA, SymbolT, NFAStateT
from my_automata.utils import (
    binary_strings_with_wildcard,
    dot_product_with_wildcard,
    apply_mask,
    intersection_containing_wildcard,
)


# 各リテラルに対してnfaを作成するクラス
class AutomataBuilder:
    INITIAL_STATE = "q0"

    def __init__(self, coefs: list[str], const: int, relation: str, mask: list[bool], create_all: bool = False) -> None:
        if len(coefs) != len(mask):
            raise ValueError("The length of the mask must be equal to the length of the coefficients")
        self.coefs = coefs
        self.const = const
        self.relation = relation
        self.mask = mask
        self.create_all = create_all  # for debug
        self.nfa = NFA(
            states={self.INITIAL_STATE, str(self.const)},
            input_symbols=binary_strings_with_wildcard(self.mask),
            transitions=defaultdict(lambda: defaultdict(set)),
            initial_state=self.INITIAL_STATE,
            final_states=set([str(self.const)]),
        )
        self.work_list = [self.const]

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
        return partial_sat

    # def neq_to_nfa(a: list[int], c: int) -> None:
    #     pass


# TODO: タプルのネストを外す。tuple(itertools.chain.from_iterable(tup;e))でいける
def nfa_intersection(nfa1: NFA, nfa2: NFA, mask1: list[bool], mask2: list[bool]) -> tuple[NFA, list[bool]]:
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

    new_mask = [x or y for x, y in zip(mask1, mask2)]

    return (nfa, new_mask)
