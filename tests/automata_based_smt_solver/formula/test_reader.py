from pysmt.fnode import FNode

from absmt.sat_status import SatStatus


class TestReader:
    def test_from_smt_lib_file(self, reader, benchmark_file_paths):
        """Test reading from SMT-LIB files."""
        for file_path in benchmark_file_paths:
            # Convert Path to string for pysmt compatibility
            file_path_str = str(file_path)

            # Test each benchmark file
            status, formula = reader.from_smt_lib(file_path_str, is_file_path=True)

            # Check formula basics (should work for all files)
            assert isinstance(formula, FNode)

            # Check that variables are properly extracted
            variables = formula.get_free_variables()
            assert len(variables) > 0, f"No variables found in {file_path.name}"

    def test_status_from_smt_files(self, reader, benchmark_files_by_status):
        """Test that status is correctly parsed from SMT-LIB files."""
        files, expected_status = benchmark_files_by_status

        for file_path in files:
            # Convert Path to string for pysmt compatibility
            file_path_str = str(file_path)

            status, _ = reader.from_smt_lib(file_path_str, is_file_path=True)
            assert status == SatStatus(expected_status), (
                f"Wrong status for {file_path.name}"
            )

    def test_from_smt_lib_string(self, reader):
        """Test reading from an SMT-LIB string."""
        smt_content = """
        (set-info :smt-lib-version 2.6)
        (set-info :status sat)
        (declare-fun x () Int)
        (declare-fun y () Int)
        (assert (= x y))
        (check-sat)
        """
        status, formula = reader.from_smt_lib(smt_content, is_file_path=False)

        # Check status
        assert status == SatStatus.SAT

        # Check formula
        assert isinstance(formula, FNode)
        assert formula.is_equals()

        # Check variables
        variables = formula.get_free_variables()
        variable_names = {str(var) for var in variables}
        assert variable_names == {"x", "y"}

    def test_unknown_status(self, reader):
        """Test reading a formula with unknown status."""
        smt_content = """
        (declare-fun x () Int)
        (assert (> x 0))
        (check-sat)
        """
        status, formula = reader.from_smt_lib(smt_content, is_file_path=False)

        # Status should be unknown as there's no status info
        assert status == SatStatus.UNKNOWN

        # Check formula
        assert isinstance(formula, FNode)

    def test_parsed_formula_fixture(self, int_incompleteness1_formula):
        """Test using the parsed_formula fixture from conftest."""
        # Verify the formula is parsed correctly
        assert isinstance(int_incompleteness1_formula, FNode)

        # Verify it's the expected formula (bignum_lia1.smt2)
        variables = int_incompleteness1_formula.get_free_variables()
        variable_names = {str(var) for var in variables}
        expected_vars = {"x1", "x2"}
        assert variable_names == expected_vars

    def test_all_parsed_formulas_fixture(self, all_parsed_formulas):
        """Test using the all_parsed_formulas fixture from conftest."""
        # Verify we got formula data for all files
        assert len(all_parsed_formulas) > 0

        for filename, formula in all_parsed_formulas:
            # Every formula should be an FNode
            assert isinstance(formula, FNode)

            # Every formula should have variables
            variables = formula.get_free_variables()
            assert len(variables) > 0, f"No variables found in {filename}"
