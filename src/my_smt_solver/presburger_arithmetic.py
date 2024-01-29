from .type import Relation


class PresburgerArithmetic:
    def __init__(self, terms: list[tuple[int, str]], relation: Relation, const: int) -> None:
        self.__terms = terms
        self.__relation = relation
        self.__const = const

    @property
    def terms(self) -> list[tuple[int, str]]:
        return self.__terms

    @terms.setter
    def terms(self, terms: list[tuple[int, str]]) -> None:
        self.__terms = terms

    def add_term(self, term: tuple[int, str]) -> None:
        self.__terms.append(term)

    @property
    def relation(self) -> Relation:
        return self.__relation

    @relation.setter
    def relation(self, relation: Relation) -> None:
        self.__relation = relation

    @property
    def const(self) -> int:
        return self.__const

    def invert(self) -> None:
        self.__relation = self.__relation.invert()
        self.__const = -self.__const
        self.__terms = [(-value, var) for value, var in self.__terms]

    def __str__(self) -> str:
        def format_term(coef: int, var: str, is_first: bool) -> str:
            sign = "" if coef >= 0 and is_first else "+" if coef >= 0 else "-"
            formatted_coef = f"{sign} {abs(coef)}" if not is_first else f"{coef}"
            return f"{formatted_coef}{var}"

        terms_list = list(self.__terms)
        left_side_terms = (format_term(coef, var, index == 0) for index, (coef, var) in enumerate(terms_list))
        left_side = " ".join(left_side_terms).lstrip()

        right_side = str(self.__const)

        return f"{left_side} {self.__relation.value} {right_side}"

    def is_valid_expression(self, var_assignments: dict[str, int]) -> bool:
        if not var_assignments:
            raise ValueError("var_assignments is empty")
        lhs = 0
        for value, var in self.terms:
            lhs += value * var_assignments[var]

        if self.relation == Relation.EQ:
            return lhs == self.const
        elif self.relation == Relation.NEQ:
            return lhs != self.const
        elif self.relation == Relation.LT:
            return lhs < self.const
        elif self.relation == Relation.GT:
            return lhs > self.const
        elif self.relation == Relation.LEQ:
            return lhs <= self.const
        else:  # self.relation is Relation.GEQ
            return lhs >= self.const
