import itertools
from collections import defaultdict
from src.my_automata.my_automata import MutableNFA as NFA
import src.my_automata.my_automata as T


# 各リテラルに対してnfaを作成するクラス
class AutomataBuilder:
    WILDCARD = "*"
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
            input_symbols=self.__binary_strings_with_wildcard(),
            transitions=defaultdict(lambda: defaultdict(set)),
            initial_state=self.INITIAL_STATE,
            final_states=set([str(self.const)]),
        )
        self.work_list = [self.const]

    def next(self) -> bool:
        # TODO: self.relationによって、どの関数を呼び出すかを変えたい。relationクラスかenumを作成する
        return self.eq_to_nfa()

    def __binary_strings_with_wildcard(self) -> set[str]:
        """
        Generates binary strings with a wildcard (*) inserted at specified positions based on a mask.

        Args:
            mask: A list of booleans where True indicates that the corresponding position should be kept,
                and False indicates that the position should be removed.

        Returns:
            A set of binary strings with the wildcard (*) inserted at appropriate positions based on the mask.
        """

        # Generate combinations of "01" for the positions to keep
        combinations = list(itertools.product("01", repeat=self.mask.count(True)))
        # Convert combinations into binary strings
        binary_strings = {"".join(x) for x in combinations}

        # Iterate over the mask and insert the wildcard (*) at specified positions
        for i, is_masked in enumerate(self.mask):
            if not is_masked:
                binary_strings = {s[:i] + self.WILDCARD + s[i:] for s in binary_strings}

        return binary_strings

    def __dot_product_with_wildcard(self, coefs: list[str], symbol: T.SymbolT) -> int:
        if len(coefs) != len(symbol):
            raise ValueError("Vectors must have the same length")

        result = 0

        for v1, v2 in zip(coefs, symbol):
            if v2 != self.WILDCARD:
                result += int(v1) * int(v2)
        return result

    """
    coefs: all the coefficients of the linear equations
    const: constant of the linear equation
    """

    def eq_to_nfa(self) -> bool:
        partial_sat = False

        while self.work_list:
            current_state = self.work_list.pop()
            for symbol in self.nfa.input_symbols:
                dot = self.__dot_product_with_wildcard(self.coefs, symbol)
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


def nfa_intersection(nfa1: NFA, nfa2: NFA, mask1: list[bool], mask2: list[bool]) -> NFA:
    WILDCARD = "*"  # TODO: 定数の管理方法を考える

    def apply_mask(pattern: T.SymbolT, mask: list[bool]) -> T.SymbolT:
        if len(pattern) != len(mask):
            raise ValueError("The length of the mask must be equal to the length of the pattern")

        result = ""
        for i in range(len(mask)):
            if mask[i]:
                result += pattern[i]
            else:
                result += WILDCARD

        return result

    def symbol_intersection(symbol1: T.SymbolT, symbol2: T.SymbolT) -> T.SymbolT:
        if len(symbol1) != len(symbol2):
            raise ValueError("Symbols must have the same length")

        result = ""
        for s1, s2 in zip(symbol1, symbol2):
            if s1 != s2 and WILDCARD not in (s1, s2):
                return ""
            result += s1 if s1 != WILDCARD else s2
        return result

    def intersection_containing_wildcard(symbols1: set[T.SymbolT], symbols2: set[T.SymbolT]) -> set[T.SymbolT]:
        """
        example: if '01*' and '0*0' are given, add '010' to result
        """
        result = set()
        for s1, s2 in itertools.product(symbols1, symbols2):
            s = symbol_intersection(s1, s2)
            if s:
                result.add(s)

        return result

    initial_state = (nfa1.initial_state, nfa2.initial_state)
    nfa = NFA(
        states=set(),
        input_symbols=intersection_containing_wildcard(nfa1.input_symbols, nfa2.input_symbols),
        transitions=defaultdict(lambda: defaultdict(set)),
        initial_state=initial_state,
        final_states=set(),
    )
    work_list: list[T.NFAStateT] = [initial_state]

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

    return nfa
