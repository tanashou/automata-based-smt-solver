# need path from 'src'. otherwise, pytest cannot find the module
from my_smt_solver import (
    make_binary_wildcard_strings,
    dot_product_with_wildcard,
    apply_mask,
    decode_symbols_to_int,
)
import pytest


# Test cases for the function binary_strings_with_wildcard
class TestBinaryWildcardString:
    def test_no_wildcards(self) -> None:
        coefs = [1, 1, 1]
        expected_output = {"000", "001", "010", "011", "100", "101", "110", "111"}
        assert make_binary_wildcard_strings(coefs) == expected_output

    def test_all_wildcards(self) -> None:
        coefs = [0, 0, 0]
        expected_output = {"***"}
        assert make_binary_wildcard_strings(coefs) == expected_output

    def test_mixed_mask(self) -> None:
        coefs = [1, 0, 1]
        expected_output = {"0*0", "0*1", "1*0", "1*1"}
        assert make_binary_wildcard_strings(coefs) == expected_output

    def test_single_true_mask(self) -> None:
        coefs = [1]
        expected_output = {"0", "1"}
        assert make_binary_wildcard_strings(coefs) == expected_output

    def test_single_false_mask(self) -> None:
        coefs = [0]
        expected_output = {"*"}
        assert make_binary_wildcard_strings(coefs) == expected_output


# Test cases for the function dot_product_with_wildcard
class TestDotProductWithWildcard:
    def test_all_values_no_wildcard(self) -> None:
        coefs = [1, 0, 1]
        assert dot_product_with_wildcard(coefs, "101") == 2

    def test_with_wildcards(self) -> None:
        coefs = [1, 1, 1]
        assert dot_product_with_wildcard(coefs, "1*1") == 2

    def test_all_wildcards(self) -> None:
        coefs = [1, 1, 1]
        assert dot_product_with_wildcard(coefs, "***") == 0

    def test_empty_lists(self) -> None:
        coefs: list[int] = []
        assert dot_product_with_wildcard([], "") == 0

    def test_mismatched_length(self) -> None:
        coefs = [1, 0]
        with pytest.raises(ValueError):
            dot_product_with_wildcard(coefs, "101")


class TestApplyMask:
    def test_all_wildcards(self) -> None:
        pattern = "101"
        mask = [False, False, False]
        assert apply_mask(pattern, mask) == "***"

    def test_no_wildcards(self) -> None:
        pattern = "101"
        mask = [True, True, True]
        assert apply_mask(pattern, mask) == "101"

    def test_mixed_mask(self) -> None:
        pattern = "101"
        mask = [True, False, True]
        assert apply_mask(pattern, mask) == "1*1"


class TestDecodeSymbolsToInt:
    def test_decode_symbols_to_int(self) -> None:
        assert decode_symbols_to_int(["0", "1", "0", "1"]) == [5]
        assert decode_symbols_to_int(["0001", "1001", "0011"]) == [2, 0, 1, -1]
        # Test case 3: Case with wildcard
        symbols = ["*01", "*11", "*10"]
        with pytest.raises(ValueError):
            decode_symbols_to_int(symbols)
