from my_smt_solver.automata_builder import AutomataBuilder
from my_smt_solver.utils import *

# 将来的には pySMT で変数や式を定義する
# x = Symbol("x")
# y = Symbol("y")
# z = Symbol("z")
# eq = Eq(sp.Add(x, y, sp.Mul(4, z)), 10)
# # eq.free_symbols は変数だけ返したいのに不適。
# vars_index_map = {var: idx for idx, var in enumerate(eq.atoms(Symbol))}
# print(vars_index_map)
# print(eq)
# # Eq の戻り値に Relational が含まれている。これは無視する
# builder = AutomataBuilder(eq, vars_index_map)  # type: ignore[arg-type]
# print(builder.coefs)
# print(builder.const)
# print(builder.relation)
# print(builder.nfa)
# builder.next()
# builder.nfa.show_diagram("test.png")
# builder.next()
# builder.nfa.show_diagram("test2.png")
from parser.smt_to_sympy import SMTToSymPy

smt_file_path = "benchmarks/QF_LIA/prime-cone/prime_cone_sat_2.smt2"


smt2sympy = SMTToSymPy(source=smt_file_path, is_file=True)
sympy_expr_dnf = smt2sympy.get_sympy_expression_as_dnf()
for formula in sympy_expr_dnf.args:
    builder = AutomataBuilder(formula, smt2sympy.declared_vars_index_map)
    while not builder.build_completed:
        builder.next()
    print(formula)
