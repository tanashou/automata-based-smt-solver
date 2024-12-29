class InputSymbol(str):
    __slots__ = ("bin_length", "mask", "masked_value", "value")
    """Represents an input symbol with optional mask.

    value and mask are binary strings like "1010" or empty string for epsilon.
    """

    def __new__(cls, value: str, mask: str) -> "InputSymbol":
        if value and not mask:
            msg = "Non-epsilon symbol must have a mask"
            raise ValueError(msg)
        if not value and mask:
            msg = "Epsilon symbol cannot have a mask"
            raise ValueError(msg)
        if len(value) != len(mask):
            msg = "Value and mask must have the same length"
            raise ValueError(msg)

        obj = str.__new__(cls, value)
        obj.value = int(value, 2) if value else None
        obj.mask = int(mask, 2) if mask else None
        obj.masked_value = obj.apply_mask()
        obj.bin_length = len(value)
        return obj

    def __hash__(self) -> int:
        if self.is_epsilon():
            return hash(None)
        return hash((self.value, self.mask))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, InputSymbol):
            return self.masked_value == other.masked_value
        return False

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
        val_bits = val_bits.zfill(self.bin_length)
        mask_bits = mask_bits.zfill(self.bin_length)

        # Create result string using mask
        return "".join(
            val_bits[i] if mask_bits[i] == "1" else "*" for i in range(self.bin_length)
        )

    def __repr__(self) -> str:
        """Return string representation for collections."""
        return self.__str__()

    def is_epsilon(self) -> bool:
        return self.value is None

    def apply_mask(self) -> int | None:
        if self.is_epsilon():
            return None
        return self.value & self.mask  # type: ignore[union-attr]

    def dot(self, vector: list[int]) -> int:
        if self.masked_value is None:
            msg = "Cannot calculate dot product with epsilon symbol"
            raise ValueError(msg)

        if self.bin_length > len(vector):
            msg = "Vector length is smaller than the number of bits in value"
            raise ValueError(msg)

        result = 0
        for i, v in enumerate(reversed(vector)):
            if self.masked_value & (1 << i):
                result += v
        return result


# create epsilon as a singleton
EPSILON = InputSymbol(value="", mask="")
