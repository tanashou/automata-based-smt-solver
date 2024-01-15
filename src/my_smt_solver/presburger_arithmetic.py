from .type import Relation


class PresburgerArithmetic:
    def __init__(self, terms: list[tuple[str, int]], relation: Relation, const: int) -> None:
        self.__terms = terms
        self.__relation = relation
        self.__const = const

    @property
    def terms(self) -> list[tuple[str, int]]:
        return self.__terms

    @terms.setter
    def terms(self, terms: list[tuple[str, int]]) -> None:
        self.__terms = terms

    def add_term(self, term: tuple[str, int]) -> None:
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


    def __str__(self) -> str:
        def format_term(coef, var, is_first):
            sign = "" if coef >= 0 and is_first else "+" if coef >= 0 else "-"
            formatted_coef = f"{sign} {abs(coef)}" if not is_first else f"{coef}"
            return f"{formatted_coef}{var}"

        terms_list = list(self.__terms)
        left_side_terms = (format_term(coef, var, index == 0) for index, (var, coef) in enumerate(terms_list))
        left_side = " ".join(left_side_terms).lstrip()

        right_side = str(self.__const)

        return f"{left_side} {self.__relation.value} {right_side}"

    def is_valid_expression(self, var_assignments: dict[str, int]) -> bool:
        if not var_assignments:
            raise ValueError("var_assignments is empty")
        rhs = 0
        for var, value in self.terms:
            rhs += value * var_assignments[var]

        if self.relation == Relation.EQ:
            return rhs == self.const
        elif self.relation == Relation.NEQ:
            return rhs != self.const
        elif self.relation == Relation.LT:
            return rhs < self.const
        elif self.relation == Relation.GT:
            return rhs > self.const
        elif self.relation == Relation.LEQ:
            return rhs <= self.const
        else:  # self.relation is Relation.GEQ
            return rhs >= self.const
