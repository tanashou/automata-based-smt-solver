from uuid import UUID


class State:
    DEFAULT_UUID = UUID(int=0)

    def __init__(
        self,
        state_value: str | int,
        uuid: UUID | None = None,
    ) -> None:
        # 状態の値が同じでも別々に区別するためにuuidを持つ。union で使う
        self.state_value = state_value
        self.uuid = uuid if uuid is not None else self.DEFAULT_UUID

    def __str__(self) -> str:
        return str(self.state_value)

    def __repr__(self) -> str:
        return self.__str__()

    def __hash__(self) -> int:
        return hash((self.uuid, self.state_value))
