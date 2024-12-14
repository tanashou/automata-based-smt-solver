import pytest

from automata_based_smt_solver.automata.input_symbol import InputSymbol


class TestInputSymbol:
    @pytest.mark.parametrize(
        ("value", "mask"), [(0b1010, 0b1111), (0b0, 0b1111), (0b1111, 0b1111)]
    )
    def test_instance_creation_with_valid_binary(self, value, mask):
        """Test creating instance with valid binary numbers and masks."""
        symbol = InputSymbol(value, mask)
        assert symbol.value == value
        assert symbol.mask == mask

    def test_epsilon_creation(self):
        """Test creating epsilon symbol."""
        epsilon = InputSymbol(None, None)
        assert epsilon.is_epsilon()
        assert str(epsilon) == "ε"

    def test_invalid_creation(self):
        """Test invalid symbol creation."""
        with pytest.raises(ValueError, match="Epsilon cannot have a mask"):
            InputSymbol(None, 0b1111)  # Epsilon with mask
        with pytest.raises(ValueError, match="Value must have a mask"):
            InputSymbol(0b1111, None)  # Value without mask

    @pytest.mark.parametrize(
        ("value1", "mask1", "value2", "mask2", "expected"),
        [
            (0b1010, 0b1111, 0b1010, 0b1111, True),
            (0b0000, 0b1111, 0b1111, 0b1111, False),
            (0b0110, 0b1110, 0b0111, 0b1110, True),
            (None, None, None, None, True),  # Epsilon comparison
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
            (0b0101, 0b1101, "01*1"),
            (0b1111, 0b1111, "1111"),
            (0b0000, 0b0000, "*"),
            (None, None, "ε"),
        ],
    )
    def test_string_representation(self, value, mask, expected_str):
        """Test string representation with masks."""
        symbol = InputSymbol(value, mask)
        assert str(symbol) == expected_str

    def test_hash_consistency(self):
        """Test hash consistency."""
        symbol1 = InputSymbol(0b1010, 0b1111)
        symbol2 = InputSymbol(0b1010, 0b1111)
        assert hash(symbol1) == hash(symbol2)

        epsilon1 = InputSymbol(None, None)
        epsilon2 = InputSymbol(None, None)
        assert hash(epsilon1) == hash(epsilon2)

    @pytest.mark.parametrize(
        ("value", "mask", "vector", "expected"),
        [
            (0b1010, 0b1111, [1, 2, 3, 4], 4),
            (0b1100, 0b1111, [1, 1, 1, 1], 2),
        ],
    )
    def test_dot_product(self, value, mask, vector, expected):
        """Test dot product calculation."""
        symbol = InputSymbol(value, mask)
        assert symbol.dot(vector) == expected

    def test_dot_product_epsilon_error(self):
        """Test dot product with epsilon raises error."""
        epsilon = InputSymbol(None, None)
        with pytest.raises(ValueError, match="Epsilon cannot perform dot product"):
            epsilon.dot([1, 2, 3, 4])
