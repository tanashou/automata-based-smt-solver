import unittest
from src.my_automata.util import *



# Test cases for the function binary_strings_with_wildcard
class TestBinaryStringsWithWildcard(unittest.TestCase):
    def test_no_wildcards(self):
        mask = [True, True, True]
        expected_output = {"000", "001", "010", "011", "100", "101", "110", "111"}
        self.assertEqual(binary_strings_with_wildcard(mask), expected_output)

    def test_all_wildcards(self):
        mask = [False, False, False]
        expected_output = {"***"}
        self.assertEqual(binary_strings_with_wildcard(mask), expected_output)

    def test_mixed_mask(self):
        mask = [True, False, True]
        expected_output = {"0*0", "0*1", "1*0", "1*1"}
        self.assertEqual(binary_strings_with_wildcard(mask), expected_output)

    def test_single_true_mask(self):
        mask = [True]
        expected_output = {"0", "1"}
        self.assertEqual(binary_strings_with_wildcard(mask), expected_output)

    def test_single_false_mask(self):
        mask = [False]
        expected_output = {"*"}
        self.assertEqual(binary_strings_with_wildcard(mask), expected_output)


if __name__ == "__main__":
    unittest.main()
