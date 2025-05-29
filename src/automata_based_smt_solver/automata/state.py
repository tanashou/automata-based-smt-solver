from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class State:
    # 同じ状態でも区別するためにidを持つ。union で使う。
    state_value: Any
    id: int

    def __post_init__(self) -> None:
        if isinstance(self.state_value, State):
            # Save the original state's id before modifying state_value
            original_state = self.state_value
            inner_value = original_state.state_value
            object.__setattr__(self, "state_value", inner_value)

    def __hash__(self) -> int:
        return hash((self.state_value, self.id))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, State):
            return self.state_value == other.state_value and self.id == other.id
        return False

    def __str__(self) -> str:
        return f"{self.state_value}({self.id})"

    def __repr__(self) -> str:
        return self.__str__()
