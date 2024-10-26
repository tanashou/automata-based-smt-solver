from parser.smt_to_sympy import SMTToSymPy

smt_file_path = "benchmarks/QF_LIA/prime-cone/prime_cone_sat_2.smt2"


smt2sympy = SMTToSymPy(source=smt_file_path, is_file=True)
sympy_expr_dnf = smt2sympy.get_sympy_expression_as_dnf()
print(smt2sympy.declared_vars)
print(sympy_expr_dnf)
print(smt2sympy.sat_status)

components = list(sympy_expr_dnf.args)
for c in components:
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
