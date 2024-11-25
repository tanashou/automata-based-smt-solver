class InputSymbol:
    def __init__(self, value: int) -> None:
        self.value = value

    def dot(self, vector: list[int]) -> int:
        result = 0
        value = self.value

        for i, v in enumerate(reversed(vector)):
            if value & (1 << i):
                result += v
        return result

    def apply_mask(self, mask: int) -> int:
        return self.value & mask
