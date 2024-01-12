from my_smt_solver import PresburgerArithmetic, Relation


class Solver:
    # Prb 算術式を受け取り、適切な式を生成する。その後、builderを呼び出す
    def __init__(self) -> None:
        self.__prb_arithmetics = []
        self.variables: list[str] = []
        self.__coefs = []

    @property
    def coefs(self) -> list[list[int]]:
        return self.__coefs

    def add(self, prb_arithmetic: PresburgerArithmetic) -> None:
        self.__prb_arithmetics.append(prb_arithmetic)

    def set_variables(self) -> None:
        var_set = set()
        for prb_arithmetic in self.__prb_arithmetics:
            vars = [term[0] for term in prb_arithmetic.terms]
            var_set.update(vars)
        if "z_neq" in var_set:
            raise ValueError("z_neq is reserved variable name")

        self.variables = sorted(var_set)


    def set_coefs(self) -> None:
        num_arithmetics = len(self.__prb_arithmetics)
        num_variables = len(self.variables)

        self.__coefs = [[0 for _ in range(num_variables)] for _ in range(num_arithmetics)]

        for arithmetic_index, prb_arithmetic in enumerate(self.__prb_arithmetics):
            for term_var, term_value in prb_arithmetic.terms:
                if term_var in self.variables:
                    var_index = self.variables.index(term_var)
                    self.__coefs[arithmetic_index][var_index] += term_value


    def __check_neq(self) -> bool:
        for prb_arithmetic in self.__prb_arithmetics:
            if prb_arithmetic.relation == Relation.NEQ:
                return True
        return False

    def check(self):
        # TODO: 変数集合を整理する
        self.set_variables()
        self.set_coefs()
