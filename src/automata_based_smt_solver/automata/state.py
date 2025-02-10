from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class State:
    # 同じ状態でも区別するためにuuidを持つ。union で使う。
    state_value: Any
    id: int = -1

    # for better usage
    def __post_init__(self) -> None:
        if isinstance(self.state_value, State):
            msg = "state_value cannot be an instance of State"
            raise TypeError(msg)

    def __hash__(self) -> int:
        return hash((self.state_value, self.id))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, State):
            return self.state_value == other.state_value and self.id == other.id
        return False

    def __str__(self) -> str:
        # intersection を取る際、id が不要。新しく作る状態に id を指定しない。
        if self.id == -1:
            return str(self.state_value)
        return f"{self.state_value}({self.id})"

    def __repr__(self) -> str:
        return self.__str__()


INITIAL_STATE = State("q0")
