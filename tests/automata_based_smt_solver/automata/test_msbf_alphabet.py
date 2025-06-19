import itertools

import pytest
from pysmt.shortcuts import Symbol
from pysmt.typing import INT

from automata_based_smt_solver.automata.msbf_alphabet import MSBFAlphabet
from automata_based_smt_solver.automata.msbf_alphabet_symbol import MSBFAlphabetSymbol


class TestMSBFAlphabet:
    def setup_method(self):
        self.a = Symbol("a", INT)
        self.b = Symbol("b", INT)
        self.c = Symbol("c", INT)
        self.d = Symbol("d", INT)
        self.e = Symbol("e", INT)

    def test_symbol_generator_partial_used_vars(self):
        all_vars = [self.a, self.b, self.c]
        used_vars = [self.a, self.b]
        mask = "110"
        symbols = list(MSBFAlphabet(all_vars, used_vars).symbol_generator())

        expected_symbols_prefix = list(itertools.product("01", repeat=len(used_vars)))
        expected = {
            MSBFAlphabetSymbol("".join(prefix) + "0", mask)
            for prefix in expected_symbols_prefix
        }
        assert set(symbols) == expected

    def test_symbol_generator_all_used_vars(self):
        all_vars = [self.a, self.b, self.c]
        used_vars = [self.a, self.b, self.c]
        mask = "111"
        symbols = list(MSBFAlphabet(all_vars, used_vars).symbol_generator())

        expected_symbols = list(itertools.product("01", repeat=len(used_vars)))
        expected = {
            MSBFAlphabetSymbol("".join(symbols), mask) for symbols in expected_symbols
        }
        assert set(symbols) == expected

    def test_symbol_generator_with_empty_used_vars(self):
        all_vars = [self.a, self.b, self.c]
        used_vars = []
        mask = "000"
        symbols = list(MSBFAlphabet(all_vars, used_vars).symbol_generator())

        expected = {MSBFAlphabetSymbol("000", mask)}
        assert set(symbols) == expected

    def test_symbol_generator_not_subset(self):
        all_vars = [self.a, self.b, self.c]
        used_vars = [self.a, self.d]
        with pytest.raises(ValueError, match="used_vars must be a subset of all_vars"):
            MSBFAlphabet(all_vars, used_vars)

    def test_has_same_symbols(self):
        # all_vars are the same, so has_same_symbols is True
        all_vars = [self.a, self.b, self.c, self.d]
        used_vars1 = [self.a, self.b, self.d]
        used_vars2 = [self.a, self.b, self.c]
        alphabet1 = MSBFAlphabet(all_vars, used_vars1)
        alphabet2 = MSBFAlphabet(all_vars, used_vars2)
        assert alphabet1.has_same_symbols(alphabet2)
        # If all_vars differ, should be False
        diff_alphabet = MSBFAlphabet([*all_vars, self.e], used_vars1)
        assert not diff_alphabet.has_same_symbols(alphabet1)

    def test_union_alphabet(self):
        all_vars = [self.a, self.b, self.c]
        used_vars1 = [self.a, self.b]
        used_vars2 = [self.b, self.c]
        alphabet1 = MSBFAlphabet(all_vars, used_vars1)
        alphabet2 = MSBFAlphabet(all_vars, used_vars2)

        unioned = MSBFAlphabet.union_alphabet(alphabet1, alphabet2)
        assert unioned.all_vars == all_vars
        assert unioned.used_vars == [self.a, self.b, self.c]

        # If all_vars differ, should raise ValueError
        with pytest.raises(ValueError, match="Alphabets must have the same all_vars"):
            MSBFAlphabet.union_alphabet(alphabet1, MSBFAlphabet([self.d], [self.d]))

    def test_decode_symbol(self):
        all_vars = [self.a, self.b, self.c]
        used_vars = [self.a, self.b]
        alphabet = MSBFAlphabet(all_vars, used_vars)

        # a: 0b0011, b: 0b1101, c: None
        symbols = [
            MSBFAlphabetSymbol("010", "110"),
            MSBFAlphabetSymbol("010", "110"),
            MSBFAlphabetSymbol("100", "110"),
            MSBFAlphabetSymbol("110", "110"),
        ]
        decoded = alphabet.decode_symbol(symbols)

        expected = {
            self.a: 3,
            self.b: -3,
            self.c: None,
        }
        assert decoded == expected
