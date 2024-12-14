from dataclasses import dataclass


@dataclass(frozen=True)
class InputSymbol:
    # None represents epsilon symbol
    value: int | None

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, InputSymbol):
            return self.value == other.value
        return False

    def __str__(self) -> str:
        # remove the prefix "0b" from the binary representation
        return bin(self.value)[2:] if self.value is not None else ""

    def dot(self, vector: list[int]) -> int:
        if self.value is None:
            msg = "Cannot calculate dot product with epsilon symbol"
            raise ValueError(msg)

        bit_length = self.value.bit_length()
        if bit_length > len(vector):
            msg = "Vector length is smaller than the number of bits in value"
            raise ValueError(msg)

        result = 0
        value = self.value

        for i, v in enumerate(reversed(vector)):
            if value & (1 << i):
                result += v
        return result

    def apply_mask(self, mask: int) -> int:
        if self.value is None:
            msg = "Cannot apply mask to epsilon symbol"
            raise ValueError(msg)
        return self.value & mask


# create epsilon as a singleton
EPSILON = InputSymbol(None)
