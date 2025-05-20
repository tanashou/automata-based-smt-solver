from automata_based_smt_solver.solver import SMTLIBReader, Solver


class TestSolver:
    def setup_method(self):
        self.reader = SMTLIBReader()
        self.solver = Solver()

    def test_extract_data(self):
        pass
