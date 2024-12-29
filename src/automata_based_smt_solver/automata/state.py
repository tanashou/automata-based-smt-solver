from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class State:
    # 同じ状態でも区別するためにuuidを持つ。union で使う。
    state_value: Any
    uuid: UUID = field(default_factory=lambda: UUID(int=0))

    def __hash__(self) -> int:
        return hash((self.state_value, self.uuid))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, State):
            return self.state_value == other.state_value and self.uuid == other.uuid
        return False

    def __str__(self) -> str:
        return str(self.state_value)

    def __repr__(self) -> str:
        return self.__str__()
