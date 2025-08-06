from dataclasses import dataclass


@dataclass(slots=True)
class MSBFAlphabetSymbol:
    """MSBFAlphabetSymbol represents an input symbol without epsilon with mask.

    TODO: More details about the class.
    needed to inherit str class to make image of automata using automata-lib

    Attributes:
        value (int): Integer conversion of bin_value (none for epsilon).
        mask (int): Integer conversion of bin_mask (none for epsilon).
        bin_length (int): Length of the binary strings.

    """

    value: int
    mask: int
    bin_length: int = 0

    def __init__(self, bin_value: str, bin_mask: str) -> None:
        """Create a new MSBFAlphabetSymbol instance.

        Args:
            bin_value (str): Binary value string.
            bin_mask (str): Mask string (must match bin_value's length).

        Raises:
            ValueError: If bin_value or bin_mask is empty.
            ValueError: If bin_value and bin_mask have different lengths.

        Returns:
            MSBFAlphabetSymbol: A new MSBFAlphabetSymbol instance.

        """
        if not bin_value or not bin_mask:
            msg = "Both bin_value and bin_mask must be non-empty strings."
            raise ValueError(msg)
        if len(bin_value) != len(bin_mask):
            msg = "Value and mask must have the same length"
            raise ValueError(msg)
        self.value = int(bin_value, 2)
        self.mask = int(bin_mask, 2)
        self.bin_length = len(bin_value)

    def __hash__(self) -> int:
        """Calculate the hash of this MSBFAlphabetSymbol."""
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

        if self.bin_length != other.bin_length:
            return False

        combined_mask = self.mask & other.mask
        return (self.value & combined_mask) == (other.value & combined_mask)

    def __str__(self) -> str:
        """Convert to string representation using the mask.

        Examples:
            value=0b0101, mask=0b1101 -> "01*1"

        """
        val_bits = bin(self.value)[2:].zfill(self.bin_length)
        mask_bits = bin(self.mask)[2:].zfill(self.bin_length)

        return "".join(
            val_bits[i] if mask_bits[i] == "1" else "*" for i in range(self.bin_length)
        )

    def apply_mask(self) -> int:
        """Apply the mask to the symbol's value."""
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
