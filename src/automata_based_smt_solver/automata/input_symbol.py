class InputSymbol(str):
    __slots__ = ("bin_length", "mask", "masked_value", "value")
    """Represents an input symbol with optional mask.

    value and mask are binary strings like "1010" or empty string for epsilon.
    """

    def __new__(cls, bin_value: str, bin_mask: str) -> "InputSymbol":
        if bin_value and not bin_mask:
            msg = "Non-epsilon symbol must have a mask"
            raise ValueError(msg)
        if not bin_value and bin_mask:
            msg = "Epsilon symbol cannot have a mask"
            raise ValueError(msg)
        if len(bin_value) != len(bin_mask):
            msg = "Value and mask must have the same length"
            raise ValueError(msg)

        obj = str.__new__(cls, bin_value)
        obj.value = int(bin_value, 2) if bin_value else None
        obj.mask = int(bin_mask, 2) if bin_mask else None
        obj.masked_value = obj.apply_mask()
        obj.bin_length = len(bin_value)
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

        if self.value is None or self.mask is None:
            msg = "Value and mask must not be None"
            raise ValueError(msg)

        val_bits = bin(self.value)[2:].zfill(self.bin_length)
        mask_bits = bin(self.mask)[2:].zfill(self.bin_length)

        return "".join(
            val_bits[i] if mask_bits[i] == "1" else "*" for i in range(self.bin_length)
        )

    def __repr__(self) -> str:
        return self.__str__()

    def is_epsilon(self) -> bool:
        return self.value is None

    def apply_mask(self) -> int | None:
        if self.is_epsilon():
            return None
        return self.value & self.mask  # type: ignore[union-attr]

    def dot(self, var_coef_index_pairs: list[tuple[int, int]]) -> int:
        if self.masked_value is None:
            msg = "Cannot calculate dot product with epsilon symbol"
            raise ValueError(msg)

        result = 0
        for coeff, index in var_coef_index_pairs:
            # Adjust the index: leftmost bit is index 0.
            if (self.masked_value >> (self.bin_length - index - 1)) & 1:
                result += coeff

        return result


# create epsilon as a singleton
EPSILON = InputSymbol(bin_value="", bin_mask="")
