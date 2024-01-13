from my_smt_solver import PresburgerArithmetic, Relation


class Solver:
    # Prb 算術式を受け取り、適切な式を生成する。その後、builderを呼び出す
    def __init__(self) -> None:
        self.__prb_arithmetics: list[PresburgerArithmetic] = []
        self.variables: list[str] = []
        self.__coefs: list[list[int]] = []

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

    # 与えられた Prb 算術式の中に NEQ が含まれている場合、新しく変数 z_neq を追加する。x != 2 を　x + z_neq = 2　and z_neq != 0 に変換する
    def __update_prb_arithmetics(self) -> None:
        if not self.__check_neq():
            return

        for prb_arithmetic in self.prb_arithmetics:
            if prb_arithmetic.relation == Relation.NEQ:
                prb_arithmetic.relation = Relation.EQ
                prb_arithmetic.add_term(("z_neq", 1))

        self.__add(PresburgerArithmetic([("z_neq", 1)], Relation.NEQ, 0))  # add z_neq != 0
        return

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

    def __check_neq(self) -> bool:
        for prb_arithmetic in self.prb_arithmetics:
            if prb_arithmetic.relation == Relation.NEQ:
                return True
        return False

    def preparation(self) -> None:
        self.__update_prb_arithmetics()
        self.__set_variables()
        self.__set_coefs()

    def check(self) -> None:
        self.preparation()
