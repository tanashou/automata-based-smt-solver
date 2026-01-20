import pytest

from absmt.automata.msbf_alphabet_symbol import (
    MSBFAlphabetSymbol,
)


class TestMSBFAlphabetSymbol:
    @pytest.mark.parametrize(
        ("bin_value", "bin_mask", "error_msg"),
        [
            (
                "1010",
                "",
                "Both bin_value and bin_mask must be non-empty strings.",
            ),
            (
                "",
                "1010",
                "Both bin_value and bin_mask must be non-empty strings.",
            ),
            (
                "101",
                "1111",
                "Value and mask must have the same length",
            ),
            (
                "1100",
                "101",
                "Value and mask must have the same length",
            ),
        ],
    )
    def test_invalid_creation(self, bin_value, bin_mask, error_msg):
        """Test that invalid combinations raise ValueError."""
        with pytest.raises(ValueError, match=error_msg):
            MSBFAlphabetSymbol(bin_value, bin_mask)

    @pytest.mark.parametrize(
        ("v1", "m1", "v2", "m2", "expected"),
        [
            ("1010", "1111", "1010", "1111", True),  # 1010 == 1010
            ("1010", "1111", "1011", "1111", False),  # 1010 == 1011
            ("0110", "1110", "0111", "1110", True),  # 011* == 011*
            ("01011", "11111", "00010", "10110", True),  # 01011 == 0*01*
            ("1100", "1111", "1100", "1011", True),  # 1*00 == 1*00
        ],
    )
    def test_equality(self, v1, m1, v2, m2, expected):
        """Test equality comparisons between symbols."""
        s1 = MSBFAlphabetSymbol(v1, m1)
        s2 = MSBFAlphabetSymbol(v2, m2)
        assert (s1 == s2) == expected

    @pytest.mark.parametrize(
        ("value", "mask", "expected_str"),
        [
            ("0101", "1101", "01*1"),
            ("1111", "1111", "1111"),
            ("0000", "0000", "****"),
            ("1010", "1010", "1*1*"),
            ("1100", "1011", "1*00"),
        ],
    )
    def test_string_representation(self, value, mask, expected_str):
        """Test that string conversion shows masked bits correctly."""
        s = MSBFAlphabetSymbol(value, mask)
        assert str(s) == expected_str

    def test_hash_consistency(self):
        """Test that identical instance of symbols have the same hash."""
        s1 = MSBFAlphabetSymbol("1010", "1111")
        s2 = MSBFAlphabetSymbol("1010", "1111")
        assert hash(s1) == hash(s2)

    @pytest.mark.parametrize(
        ("value", "mask", "coef_index_pairs", "expected"),
        [
            ("1010", "1111", [(1, 0), (2, 1), (3, 2), (4, 3)], 4),
            ("1100", "1111", [(1, 0), (1, 1), (1, 2), (1, 3)], 2),
            ("1111", "1001", [(2, 0), (3, 1), (5, 2), (7, 3)], 9),
            ("0110", "1001", [(2, 0), (3, 1), (5, 2), (7, 3)], 0),
        ],
    )
    def test_dot_product(self, value, mask, coef_index_pairs, expected):
        """Test dot product calculation with various cases."""
        s = MSBFAlphabetSymbol(value, mask)
        assert s.dot(coef_index_pairs) == expected

    def test_dot_product_empty(self):
        """Test that dot product with an empty list returns 0."""
        s = MSBFAlphabetSymbol("1010", "1111")
        assert s.dot([]) == 0
