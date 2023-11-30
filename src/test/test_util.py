import unittest
# need path start from src. otherwise, won't work
from src.my_automata.utils import binary_strings_with_wildcard, dot_product_with_wildcard


# Test cases for the function binary_strings_with_wildcard
class TestBinaryStringsWithWildcard(unittest.TestCase):
    def test_no_wildcards(self) -> None:
        mask = [True, True, True]
        expected_output = {"000", "001", "010", "011", "100", "101", "110", "111"}
        self.assertEqual(binary_strings_with_wildcard(mask), expected_output)

    def test_all_wildcards(self) -> None:
        mask = [False, False, False]
        expected_output = {"***"}
        self.assertEqual(binary_strings_with_wildcard(mask), expected_output)

    def test_mixed_mask(self) -> None:
        mask = [True, False, True]
        expected_output = {"0*0", "0*1", "1*0", "1*1"}
        self.assertEqual(binary_strings_with_wildcard(mask), expected_output)

    def test_single_true_mask(self) -> None:
        mask = [True]
        expected_output = {"0", "1"}
        self.assertEqual(binary_strings_with_wildcard(mask), expected_output)

    def test_single_false_mask(self) -> None:
        mask = [False]
        expected_output = {"*"}
        self.assertEqual(binary_strings_with_wildcard(mask), expected_output)


class TestDotProductWithWildcard(unittest.TestCase):
    def test_all_values_no_wildcard(self) -> None:
        self.assertEqual(dot_product_with_wildcard(["1", "0", "1"], "101"), 2)

    def test_with_wildcards(self) -> None:
        self.assertEqual(dot_product_with_wildcard(["1", "1", "1"], "1*1"), 2)

    def test_all_wildcards(self) -> None:
        self.assertEqual(dot_product_with_wildcard(["1", "1", "1"], "***"), 0)

    def test_empty_lists(self) -> None:
        self.assertEqual(dot_product_with_wildcard([], ""), 0)

    def test_mismatched_length(self) -> None:
        with self.assertRaises(ValueError):
            dot_product_with_wildcard(["1", "0"], "101")

    def test_invalid_input(self) -> None:
        with self.assertRaises(ValueError):
            dot_product_with_wildcard(["1", "a", "1"], "101")


if __name__ == "__main__":
    unittest.main()
