from my_smt_solver import PresburgerArithmetic, Relation


class Solver:
    # Prb 算術式を受け取り、適切な式を生成する。その後、builderを呼び出す
    def __init__(self) -> None:
        self.__prb_arithmetics = []
        self.variables: list[str] = []
        self.__coefs = []

    @property
    def prb_arithmetics(self) -> list[PresburgerArithmetic]:
        return self.__prb_arithmetics

    @property
    def coefs(self) -> list[list[int]]:
        return self.__coefs

    def add(self, prb_arithmetic: PresburgerArithmetic) -> None:
        self.__prb_arithmetics.append(prb_arithmetic)

    def set_variables(self) -> None:
        var_set = set()
        for prb_arithmetic in self.prb_arithmetics:
            vars = [term[0] for term in prb_arithmetic.terms]
            var_set.update(vars)
        if "z_neq" in var_set:
            raise ValueError("z_neq is reserved variable name")

        self.variables = sorted(var_set)

    def set_coefs(self) -> None:
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
            if prb_arithmetic.relation.name == Relation.NEQ.name:  # FIXME: when removing .name, it does't work. WTF
                return True
        return False

    # 与えられた Prb 算術式の中に NEQ が含まれている場合、新しく変数 z_neq を追加する。それに伴い、coefs を更新する
    def update_coefs_for_neq(self) -> None:
        if not self.__check_neq():
            return

        self.variables.append("z_neq")  # TODO: z_neq を定数として定義する
        for arithmetic_index, prb_arithmetic in enumerate(self.prb_arithmetics):
            if prb_arithmetic.relation.name == Relation.NEQ.name: #FIXME: WTF
                self.__coefs[arithmetic_index].append(1)
            else:
                self.__coefs[arithmetic_index].append(0)

    def check(self):
        # TODO: 変数集合を整理する
        self.set_variables()
        self.set_coefs()
