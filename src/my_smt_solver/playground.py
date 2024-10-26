from sympy import Eq, Ne
from sympy.abc import x, y, z

from my_smt_solver.automata_builder import AutomataBuilder
from my_smt_solver.utils import *

eq = Eq(x + y + 4 * z, 10)
print(Ne(x, 0).rel_op)
vars_index_map = {var: idx for idx, var in enumerate(eq.free_symbols)}
print(vars_index_map)
print(eq)
builder = AutomataBuilder(eq, vars_index_map)
print(builder.coefs)
print(builder.const)
print(builder.relation)
print(builder.nfa)
builder.next()
builder.nfa.show_diagram("test.png")
builder.next()
builder.nfa.show_diagram("test2.png")
