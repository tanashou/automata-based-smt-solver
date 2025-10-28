from absmt.formula.smtlib_reader import SMTLIBReader
from absmt.solver import Solver


class TestSolver:
    def setup_method(self):
        self.reader = SMTLIBReader()
        self.solver = Solver()

    def test_extract_data(self):
        pass
