import pytest

from automata_based_smt_solver.automata.input_symbol import EPSILON, InputSymbol


class TestInputSymbol:
    def test_epsilon_creation(self):
        """Test creating epsilon symbol."""
        assert EPSILON.is_epsilon()
        assert str(EPSILON) == ""

    def test_invalid_creation(self):
        """Test invalid symbol creation."""
        with pytest.raises(ValueError, match="Non-epsilon symbol must have a mask"):
            InputSymbol("1111", "")  # Value without mask
        with pytest.raises(ValueError, match="Epsilon symbol cannot have a mask"):
            InputSymbol("", "1111")  # Epsilon with mask

    @pytest.mark.parametrize(
        ("value1", "mask1", "value2", "mask2", "expected"),
        [
            ("1010", "1111", "1010", "1111", True),
            ("0000", "1111", "1111", "1111", False),
            ("0110", "1110", "0111", "1110", True),
            ("", "", "", "", True),  # Epsilon comparison
        ],
    )
    def test_equality(self, value1, mask1, value2, mask2, expected):
        """Test equality with masks."""
        symbol1 = InputSymbol(value1, mask1)
        symbol2 = InputSymbol(value2, mask2)
        assert (symbol1 == symbol2) == expected

    @pytest.mark.parametrize(
        ("value", "mask", "expected_str"),
        [
            ("0101", "1101", "01*1"),
            ("1111", "1111", "1111"),
            ("0000", "0000", "****"),
            ("", "", ""),
        ],
    )
    def test_string_representation(self, value, mask, expected_str):
        """Test string representation with masks."""
        symbol = InputSymbol(value, mask)
        assert str(symbol) == expected_str

    def test_hash_consistency(self):
        """Test hash consistency."""
        symbol1 = InputSymbol("1010", "1111")
        symbol2 = InputSymbol("1010", "1111")
        assert hash(symbol1) == hash(symbol2)

        epsilon1 = InputSymbol("", "")
        epsilon2 = InputSymbol("", "")
        assert hash(epsilon1) == hash(epsilon2)

    @pytest.mark.parametrize(
        ("value", "mask", "vector", "expected"),
        [
            ("1010", "1111", [1, 2, 3, 4], 4),
            ("1100", "1111", [1, 1, 1, 1], 2),
        ],
    )
    def test_dot_product(self, value, mask, vector, expected):
        """Test dot product calculation."""
        symbol = InputSymbol(value, mask)
        assert symbol.dot(vector) == expected

    def test_dot_product_epsilon_error(self):
        """Test dot product with epsilon raises error."""
        with pytest.raises(
            ValueError, match="Cannot calculate dot product with epsilon symbol"
        ):
            EPSILON.dot([1, 2, 3, 4])
