from pysmt.smtlib.parser import SmtLibParser
from sympy import to_dnf

from parser.pysmt_to_sympy import PySMTToSymPy

# Add more walk_* methods for other operators as needed


# We read the SMT-LIB Script by creating a Parser.
# From here we can get the SMT-LIB script.
parser = SmtLibParser()

# The method SmtLibParser.get_script takes a buffer in input. We use
# StringIO to simulate an open file.
# See SmtLibParser.get_script_fname() if to pass the path of a file.
script = parser.get_script_fname(
    "benchmarks/QF_LIA/20220307-SMPT/2PhLockVParam/RC-00.smt2"
)


# The SmtLibScript provides an iterable representation of the commands
# that are present in the SMT-LIB file.
#
# Printing a summary of the issued commands
# Extract expected status from the script
# TODO: sat, unsat, unknown を定数として扱う。enum で定義する。
expected_status = None
for cmd in script.commands:
    if cmd.name == "set-info" and cmd.args[0] == ":status":
        expected_status = cmd.args[1]
        break

f = script.get_strict_formula().simplify()
print(f)
sympy_expr = PySMTToSymPy(f).get_sympy_expression()
print(sympy_expr)
dnf = to_dnf(sympy_expr)

components = list(dnf.args)
for c in components:
    print(c)
    for a in c.args:
        print(a)

# # Solve the formula using Z3
# with Solver(name="z3") as solver:
#     solver.add_assertion(f)
#     if solver.solve():
#         print("Satisfiable")
#         print("Model:")
#         for symbol in f.get_free_variables():
#             print(f"{symbol} = {solver.get_value(symbol)}")
#     else:
#         print("Unsatisfiable")
