import pytest
from automata_based_smt_solver.automata.input_symbol import InputSymbol


class TestInputSymbol:
    @pytest.mark.parametrize("binary_value", [0b1010, 0b0, 0b1111])
    def test_instance_creation_with_valid_binary(self, binary_value):
        """Test creating an instance with various valid binary numbers."""
        symbol = InputSymbol(binary_value)
        assert symbol.value == binary_value

    @pytest.mark.parametrize(
        ("binary_value", "vector", "expected_result"),
        [
            (0b1010, [1, 2, 3, 4], 4),
            (0b1100, [1, 1, 1, 1], 2),
            (0b1111, [1, 0, 1, 0], 2),
            (0b0000, [5, 6, 7, 8], 0),
            (0b1001, [2, 3, 4, 5], 7),
        ],
    )
    def test_dot(self, binary_value, vector, expected_result):
        """Test the dot method with various binary values and vectors."""
        symbol = InputSymbol(binary_value)
        result = symbol.dot(vector)
        assert result == expected_result

    @pytest.mark.parametrize(
        ("binary_value", "mask", "expected_result"),
        [
            (0b1010, 0b1100, 0b1000),
            (0b1111, 0b1010, 0b1010),
            (0b0000, 0b1111, 0b0000),
            (0b1101, 0b1001, 0b1001),
            (0b0110, 0b0011, 0b0010),
        ],
    )
    def test_apply_mask_method(self, binary_value, mask, expected_result):
        """Test the apply_mask method with various binary values and masks."""
        symbol = InputSymbol(binary_value)
        result = symbol.apply_mask(mask)
        assert result == expected_result
