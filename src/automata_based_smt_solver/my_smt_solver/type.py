from collections import defaultdict
from enum import StrEnum
from typing import Any

import sympy
from sympy.core.relational import Relational

SymbolT = str
NFAStateT = Any  # 入れ子になる可能性があるので、Anyにしておく
NFAPathT = defaultdict[SymbolT, set[NFAStateT]]
NFATransitionT = defaultdict[NFAStateT, NFAPathT]
InputPathListT = list[tuple[NFAStateT, NFAStateT, SymbolT]]

PrbExpr = Relational | sympy.And | sympy.Or


class Relation(StrEnum):
    EQ = "="  # Equals
    NEQ = "!="  # Not Equals
    LT = "<"  # Less Than
    GT = ">"  # Greater Than
    LEQ = "<="  # Less than or Equal to
    GEQ = ">="  # Greater than or Equal to

    @classmethod
    def from_str(cls, relation_str: str) -> "Relation":
        for relation in cls:
            if relation.value == relation_str:
                return relation
        raise ValueError(f"Invalid relation: {relation_str}")

    def flip(self) -> "Relation":
        match self:
            case Relation.LT:
                return Relation.GT
            case Relation.GT:
                return Relation.LT
            case Relation.LEQ:
                return Relation.GEQ
            case Relation.GEQ:
                return Relation.LEQ
            case _:
                raise ValueError("Cannot flip the relation")
