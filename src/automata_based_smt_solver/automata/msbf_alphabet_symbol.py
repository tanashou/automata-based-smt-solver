from dataclasses import dataclass


@dataclass(slots=True)
class MSBFAlphabetSymbol:
    """MSBFAlphabetSymbol represents an input symbol without epsilon with mask.

    TODO: More details about the class.
    needed to inherit str class to make image of automata using automata-lib

    Attributes:
        value (int | None): Integer conversion of bin_value (none for epsilon).
        mask (int | None): Integer conversion of bin_mask (none for epsilon).
        bin_length (int): Length of the binary strings.

    """

    bin_value: str
    bin_mask: str
    value: int | None = None
    mask: int | None = None
    bin_length: int = 0

    def __init__(self, bin_value: str, bin_mask: str) -> None:
        """Create a new MSBFAlphabetSymbol instance.

        Args:
            bin_value (str): Binary value string (empty for epsilon).
            bin_mask (str): Mask string (must match bin_value's length).

        Raises:
            ValueError: If a non-epsilon symbol is missing a mask.
            ValueError: If an epsilon symbol is provided with a mask.
            ValueError: If bin_value and bin_mask have different lengths.

        Returns:
            MSBFAlphabetSymbol: A new MSBFAlphabetSymbol instance.

        """
        if bin_value and not bin_mask:
            msg = "Non-epsilon symbol must have a mask"
            raise ValueError(msg)
        if not bin_value and bin_mask:
            msg = "Epsilon symbol cannot have a mask"
            raise ValueError(msg)
        if len(bin_value) != len(bin_mask):
            msg = "Value and mask must have the same length"
            raise ValueError(msg)
        self.bin_value = bin_value
        self.bin_mask = bin_mask
        self.value = int(bin_value, 2) if bin_value else None
        self.mask = int(bin_mask, 2) if bin_mask else None
        self.bin_length = len(bin_value)

    def __hash__(self) -> int:
        """Calculate the hash of this MSBFAlphabetSymbol."""
        if self.is_epsilon():
            return hash(None)
        return hash((self.value, self.mask))

    def __eq__(self, other: object) -> bool:
        """Compare this MSBFAlphabetSymbol with another for equality.

        Args:
            other (object): Another object to compare against.

        Returns:
            bool: True if both symbols are equal (including masks), False otherwise.

        """
        if not isinstance(other, MSBFAlphabetSymbol):
            return False

        # Handle epsilon symbols
        if self.is_epsilon() or other.is_epsilon():
            return self.is_epsilon() and other.is_epsilon()

        if self.bin_length != other.bin_length:
            return False

        # Both self.mask and other.mask are not None here
        if (
            self.mask is None
            or other.mask is None
            or self.value is None
            or other.value is None
        ):
            return False
        combined_mask = self.mask & other.mask
        return (self.value & combined_mask) == (other.value & combined_mask)

    def __str__(self) -> str:
        """Convert to string representation using the mask.

        Examples:
            value=0b0101, mask=0b1101 -> "01*1"
            epsilon -> "ε"

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
        """Return a string representation of the MSBFAlphabetSymbol."""
        return self.__str__()

    def __reduce__(self) -> tuple[type, tuple[str, str]]:
        return (self.__class__, (self.bin_value, self.bin_mask))

    def is_epsilon(self) -> bool:
        """Check if this symbol is an epsilon symbol."""
        return self.value is None

    def apply_mask(self) -> int:
        """Apply the mask to the symbol's value."""
        if self.is_epsilon():
            msg = "Cannot apply mask to epsilon symbol"
            raise ValueError(msg)
        if self.value is None or self.mask is None:
            msg = "Cannot apply mask if value or mask is None"
            raise ValueError(msg)
        return self.value & self.mask

    def dot(self, var_coef_index_pairs: list[tuple[int, int]]) -> int:
        """Calculate the dot product using the masked value.

        Args:
            var_coef_index_pairs (list[tuple[int, int]]):
                A list of (coefficient, index) pairs.

        Returns:
            int: The dot product result computed from the masked binary value.

        """
        result = 0
        masked_value = self.apply_mask()
        for coeff, index in var_coef_index_pairs:
            # Adjust the index: leftmost bit is index 0.
            if (masked_value >> (self.bin_length - index - 1)) & 1:
                result += coeff

        return result
