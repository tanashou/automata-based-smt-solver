from enum import Enum, auto


class BuildStatus(Enum):
    UNTOUCHED = auto()
    ONGOING = auto()
    COMPLETED = auto()
