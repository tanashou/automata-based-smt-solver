from dataclasses import dataclass
from typing import TypeAlias

NFAStateT: TypeAlias = str | int | tuple["NFAStateT", ...]


@dataclass(slots=True)
class State:
    value: NFAStateT
    has_path_to_final: bool = False

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, State):
            return False
        return self.value == other.value
