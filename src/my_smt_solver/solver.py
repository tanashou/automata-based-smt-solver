from functools import reduce
from my_smt_solver.nfa import NFA
from .presburger_arithmetic import PresburgerArithmetic
from .type import Relation
from .automata_builder import AutomataBuilder
from .utils import decode_symbols_to_int
import logging


class Solver:
    # Prb 算術式を受け取り、適切な式を生成する。その後、builderを呼び出す
    def __init__(self, create_all: bool = False) -> None:
        self.__prb_arithmetics: list[PresburgerArithmetic] = []
        self.variables: list[str] = []
        self.__coefs: list[list[int]] = []
        self.__builders: list[AutomataBuilder] = []
        self.__create_all = create_all

    @property
    def prb_arithmetics(self) -> list[PresburgerArithmetic]:
        return self.__prb_arithmetics

    @property
    def coefs(self) -> list[list[int]]:
        return self.__coefs

    def add(self, prb_arithmetic: PresburgerArithmetic) -> None:
        for _, term_var in prb_arithmetic.terms:
            if term_var == "z_neq":
                raise ValueError("z_neq is reserved variable name")
        self.__prb_arithmetics.append(prb_arithmetic)

    # add prb_arithmetic including reserved variable name
    def __add(self, prb_arithmetic: PresburgerArithmetic) -> None:
        self.__prb_arithmetics.append(prb_arithmetic)

    def __check_neq(self) -> bool:
        for prb_arithmetic in self.prb_arithmetics:
            if prb_arithmetic.relation == Relation.NEQ:
                return True
        return False

    # 与えられた Prb 算術式の中に NEQ が含まれている場合、新しく変数 z_neq を追加する。x != 2 を x + z_neq = 2 and z_neq != 0 に変換する
    def __update_prb_arithmetics(self) -> None:
        if not self.__check_neq():
            return

        for prb_arithmetic in self.prb_arithmetics:
            if prb_arithmetic.relation == Relation.NEQ:
                prb_arithmetic.relation = Relation.EQ
                prb_arithmetic.add_term((1, "z_neq"))

        self.__add(PresburgerArithmetic([(1, "z_neq")], Relation.NEQ, 0))  # add z_neq != 0
        return

    # TODO: 他の <, >, >= についても変換する
    def __format_prbs_to_leq(self) -> None:
        for prb_arithmetic in self.prb_arithmetics:
            match prb_arithmetic.relation:
                case Relation.LT:
                    prb_arithmetic.flip_ineq()
                    prb_arithmetic.relation = Relation.LEQ
                    prb_arithmetic.const -= 1
                case Relation.GT:
                    prb_arithmetic.flip_ineq()
                    prb_arithmetic.relation = Relation.LEQ
                    prb_arithmetic.const -= 1
                case Relation.GEQ:
                    prb_arithmetic.flip_ineq()

    def __set_variables(self) -> None:
        var_set = set()
        for prb_arithmetic in self.prb_arithmetics:
            vars = [term[1] for term in prb_arithmetic.terms]  # term[1] is variable name
            var_set.update(vars)

        self.variables = sorted(var_set)

    def __set_coefs(self) -> None:
        num_arithmetics = len(self.prb_arithmetics)
        num_variables = len(self.variables)

        self.__coefs = [[0 for _ in range(num_variables)] for _ in range(num_arithmetics)]

        for arithmetic_index, prb_arithmetic in enumerate(self.prb_arithmetics):
            for term_value, term_var in prb_arithmetic.terms:
                if term_var in self.variables:
                    var_index = self.variables.index(term_var)
                    self.__coefs[arithmetic_index][var_index] += term_value

    def __set_builders(self) -> None:
        for coef, prb_arithmetic in zip(self.coefs, self.prb_arithmetics):
            self.__builders.append(AutomataBuilder(coef, prb_arithmetic, create_all=self.__create_all))

    def __initialize_components(self) -> None:
        self.__update_prb_arithmetics()
        self.__format_prbs_to_leq()
        self.__set_variables()
        self.__set_coefs()
        self.__set_builders()

    def __intersect_all_nfa(self) -> NFA:
        return reduce(lambda nfa1, nfa2: nfa1.intersection(nfa2), [builder.nfa for builder in self.__builders])

    def __all_builders_completed(self) -> bool:
        return all([builder.build_completed for builder in self.__builders])

    # TODO: 画像の出力を選択できるようにする
    def check(self) -> dict[str, int]:
        logging.basicConfig(filename="nfa.log", level=logging.INFO)
        self.__initialize_components()

        count = 0
        while not self.__all_builders_completed():
            for i, builder in enumerate(self.__builders):
                builder.next()
                logging.info(f"builder{i}:\n{builder.nfa}")
                builder.nfa.show_diagram(path=f"image/nfa{i}_{count}.svg")

            intersected_nfa = self.__intersect_all_nfa()
            intersected_nfa.show_diagram(path=f"image/nfa_intersection{count}.svg")

            if symbol_path := intersected_nfa.bfs_with_path():
                result = dict(zip(self.variables, decode_symbols_to_int(symbol_path)))
                print(f"sat: {result}")
                return result

        print("unsat")
        return dict()
