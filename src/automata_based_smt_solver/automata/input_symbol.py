class InputSymbol:
    def __init__(self, value: int) -> None:
        self.value = value

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, other) -> bool:
        if isinstance(other, InputSymbol):
            return self.value == other.value
        return False

    def dot(self, vector: list[int]) -> int:
        result = 0
        value = self.value

        for i, v in enumerate(reversed(vector)):
            if value & (1 << i):
                result += v
        return result

    def apply_mask(self, mask: int) -> int:
        return self.value & mask
