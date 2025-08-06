from enum import Enum, auto


class FormulaNodeType(Enum):
    AND = auto()
    OR = auto()
    ATOM = auto()
