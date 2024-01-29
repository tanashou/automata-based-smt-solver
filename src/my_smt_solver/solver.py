from functools import reduce
from my_smt_solver.nfa import NFA
from .presburger_arithmetic import PresburgerArithmetic
from .type import Relation
from .automata_builder import AutomataBuilder
from .utils import decode_symbols_to_int


class Solver:
    # Prb 算術式を受け取り、適切な式を生成する。その後、builderを呼び出す
    def __init__(self) -> None:
        self.__prb_arithmetics: list[PresburgerArithmetic] = []
        self.variables: list[str] = []
        self.__coefs: list[list[int]] = []
        self.__builders: list[AutomataBuilder] = []

    @property
    def prb_arithmetics(self) -> list[PresburgerArithmetic]:
        return self.__prb_arithmetics

    @property
    def coefs(self) -> list[list[int]]:
        return self.__coefs

    def add(self, prb_arithmetic: PresburgerArithmetic) -> None:
        for term_var, _ in prb_arithmetic.terms:
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
                prb_arithmetic.add_term(("z_neq", 1))

        self.__add(PresburgerArithmetic([("z_neq", 1)], Relation.NEQ, 0))  # add z_neq != 0
        return

    # TODO: 他の <, >, >= についても変換する
    def __format_prbs_to_leq(self) -> None:
        for prb_arithmetic in self.prb_arithmetics:
            match prb_arithmetic.relation:
                case Relation.LT:
                    pass
                case Relation.GT:
                    pass
                case Relation.GEQ:
                    pass

    def __set_variables(self) -> None:
        var_set = set()
        for prb_arithmetic in self.prb_arithmetics:
            vars = [term[0] for term in prb_arithmetic.terms]
            var_set.update(vars)

        self.variables = sorted(var_set)

    def __set_coefs(self) -> None:
        num_arithmetics = len(self.prb_arithmetics)
        num_variables = len(self.variables)

        self.__coefs = [[0 for _ in range(num_variables)] for _ in range(num_arithmetics)]

        for arithmetic_index, prb_arithmetic in enumerate(self.prb_arithmetics):
            for term_var, term_value in prb_arithmetic.terms:
                if term_var in self.variables:
                    var_index = self.variables.index(term_var)
                    self.__coefs[arithmetic_index][var_index] += term_value

    def __set_builders(self) -> None:
        for coef, prb_arithmetic in zip(self.coefs, self.prb_arithmetics):
            self.__builders.append(AutomataBuilder(coef, prb_arithmetic))

    def __initialize_components(self) -> None:
        self.__update_prb_arithmetics()
        self.__set_variables()
        self.__set_coefs()
        self.__set_builders()
        self.__components_initialized = True

    def __intersect_all_nfa(self) -> NFA:
        return reduce(lambda nfa1, nfa2: nfa1.intersection(nfa2), [builder.nfa for builder in self.__builders])

    def __all_builders_completed(self) -> bool:
        return all([builder.build_completed for builder in self.__builders])

    def check(self) -> dict[str, int]:
        self.__initialize_components()

        while not self.__all_builders_completed():
            for builder in self.__builders:
                builder.next()
            # builder.nfa.show_diagram(path=f"image/nfa{builder.relation}.png")

            intersected_nfa = self.__intersect_all_nfa()
            # intersected_nfa.show_diagram(path="image/nfa_intersection.png")

            if symbol_path := intersected_nfa.bfs_with_path():
                result = dict(zip(self.variables, decode_symbols_to_int(symbol_path)))
                print(f"sat: {result}")
                return result

        print("unsat")
        return dict()
