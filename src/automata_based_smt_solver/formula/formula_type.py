from enum import Enum, auto


class FormulaType(Enum):
    # pysmt only supports EQ, LE, and LT. We eliminated LT with walker.
    EQ = auto()
    LE = auto()
    BOOL = auto()  # Boolean variable
