from dataclasses import dataclass, field
from uuid import UUID


@dataclass(frozen=True)
class State:
    state_value: str | int
    uuid: UUID = field(default_factory=lambda: UUID(int=0))

    def __str__(self) -> str:
        return str(self.state_value)

    def __repr__(self) -> str:
        return self.__str__()
