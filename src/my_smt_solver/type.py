from collections import defaultdict
from typing import Any
from enum import StrEnum

SymbolT = str
NFAStateT = Any  # 入れ子になる可能性があるので、Anyにしておく
NFAPathT = defaultdict[SymbolT, set[NFAStateT]]
NFATransitionT = defaultdict[NFAStateT, NFAPathT]
InputPathListT = list[tuple[NFAStateT, NFAStateT, SymbolT]]


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
