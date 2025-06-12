from dataclasses import dataclass
from typing import TypeAlias

NFAStateT: TypeAlias = str | int | tuple["NFAStateT", ...]


@dataclass(slots=True)
class State:
    value: NFAStateT
    has_path_to_final: bool = False
