from enum import Enum, auto


class QuantifierType(Enum):
    NONE = auto()  # No quantifier
    FORALL = auto()  # Universal quantifier
    EXISTS = auto()  # Existential quantifier
