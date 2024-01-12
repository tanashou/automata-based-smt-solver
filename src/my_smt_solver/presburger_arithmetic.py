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

    @property
    def relation(self) -> Relation:
        return self.__relation

    @property
    def const(self) -> int:
        return self.__const
