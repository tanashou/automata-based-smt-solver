from dataclasses import dataclass


@dataclass(frozen=True)
class InputSymbol:
    # None represents epsilon symbol
    value: int | None
    mask: int | None

    def __post_init__(self) -> None:
        """Validate input symbol state."""
        if self.value is None and self.mask is not None:
            msg = "Epsilon symbol cannot have a mask"
            raise ValueError(msg)
        if self.value is not None and self.mask is None:
            msg = "Non-epsilon symbol must have a mask"
            raise ValueError(msg)

    def __hash__(self) -> int:
        if self.is_epsilon():
            return hash(None)
        return hash((self.value, self.mask))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, InputSymbol):
            return self._apply_mask() == other._apply_mask()
        return False

    # for now, 0b000 (mask: 0b000) would be "*". if the left bit is 0,
    # it would be shortened. Fix this later.
    def __str__(self) -> str:
        """Convert to string representation using mask.

        Examples:
            value=0b0101, mask=0b1101 -> "01*1"
            value=None -> "ε"

        """
        if self.is_epsilon():
            return "ε"

        # オプション型の値を使っているため、Noneチェックが必要
        if self.value is None or self.mask is None:
            msg = "Value and mask must not be None"
            raise ValueError(msg)

        # Remove '0b' prefix and pad with zeros if needed
        val_bits = bin(self.value)[2:]
        mask_bits = bin(self.mask)[2:]

        # Ensure same length by padding with zeros
        length = max(len(val_bits), len(mask_bits))
        val_bits = val_bits.zfill(length)
        mask_bits = mask_bits.zfill(length)

        # Create result string using mask
        return "".join(
            val_bits[i] if mask_bits[i] == "1" else "*" for i in range(length)
        )

    def __repr__(self) -> str:
        """Return string representation for collections."""
        return self.__str__()

    def is_epsilon(self) -> bool:
        return self.value is None

    def _apply_mask(self) -> int | None:
        if self.is_epsilon():
            return None
        return self.value & self.mask  # type: ignore[union-attr]

    def dot(self, vector: list[int]) -> int:
        value = self._apply_mask()
        if value is None:
            msg = "Cannot calculate dot product with epsilon symbol"
            raise ValueError(msg)

        bit_length = value.bit_length()
        if bit_length > len(vector):
            msg = "Vector length is smaller than the number of bits in value"
            raise ValueError(msg)

        result = 0
        for i, v in enumerate(reversed(vector)):
            if value & (1 << i):
                result += v
        return result


# create epsilon as a singleton
EPSILON = InputSymbol(value=None, mask=None)
