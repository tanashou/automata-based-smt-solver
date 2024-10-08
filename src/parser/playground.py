from pysmt.smtlib.parser import SmtLibParser
from sympy import to_dnf

from parser.smt_to_sympy import SMTToSymPy

parser = SmtLibParser()


smt_file_path = "benchmarks/QF_LIA/20220307-SMPT/2PhLockVParam/RC-00.smt2"

# TODO: sat, unsat, unknown を定数として扱う。enum で定義する。
# expected_status = None
# for cmd in script.commands:
#     if cmd.name == "set-info" and cmd.args[0] == ":status":
#         expected_status = cmd.args[1]
#         break


smt2sympy = SMTToSymPy()
smt2sympy.set_smt_script(smt_file_path, is_file=True)
sympy_expr = smt2sympy.get_sympy_expression_as_dnf()
print(sympy_expr)
dnf = to_dnf(sympy_expr)

components = list(dnf.args)
for c in components:
    print(type(c))
    print(c)

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
