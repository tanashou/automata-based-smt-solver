from my_smt_solver import PresburgerArithmetic


class Solver:
    # Prb 算術式を受け取り、適切な式を生成する。その後、builderを呼び出す
    def __init__(self) -> None:
        self.__prb_arithmetics = []
        self.variables:list[str] = []

    def add(self, prb_arithmetic: PresburgerArithmetic) -> None:
        self.__prb_arithmetics.append(prb_arithmetic)

    def set_variables(self) -> None:
        var_set = set()
        for prb_arithmetic in self.__prb_arithmetics:
            vars = [term[0] for term in prb_arithmetic.terms]
            var_set.update(vars)

        self.variables = sorted(var_set)

    def check(self):
        # TODO: 変数集合を整理する
        pass
