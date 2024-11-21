from automata_based_smt_solver.parser.neq_converter import NeqConverter
from pysmt.rewritings import CNFizer

# smt_file_path = "benchmarks/QF_LIA/convert/convert-jpg2gif-query-901.smt2"
# parser = SmtLibParser()
# smt_script = parser.get_script_fname(smt_file_path)
# formula = smt_script.get_strict_formula().simplify()
# print(formula)
# print()
from pysmt.shortcuts import (
    GE,
    LE,
    And,
    Equals,
    Int,
    Not,
    NotEquals,
    Or,
    Plus,
    Symbol,
    Times,
)
from pysmt.typing import INT

# Create integer variables
x = Symbol("x", INT)
y = Symbol("y", INT)
z = Symbol("z", INT)

# Create a QF_LIA formula
formula = And(
    LE(Plus(Times(Int(2), x), y), Int(10)),  # 2x + y <= 10
    GE(Plus(x, Times(Int(3), y)), Int(0)),  # x + 3y >= 0
    NotEquals(z, Plus(x, Times(Int(-1), y))),  # z = x - y
    Or(
        LE(z, Int(-5)),  # z <= -5
        GE(z, Int(5)),  # z >= 5
    ),
    Not(Equals(x, Int(0))),
)

# Print the original formula
print("Original formula:")
print(formula)

# Create a CNFizer instance
cnfizer = CNFizer()

# Convert the formula to CNF
cnf = cnfizer.convert_as_formula(formula)

converter = NeqConverter()
cnf = converter.walk(cnf)
# Print individual clauses
for clause in cnf.args():
    print(clause)
    for shiki in clause.args():
        print(shiki)


# Create a CNFizer instance
cnfizer = CNFizer()

# Convert the formula to CNF
cnf = cnfizer.convert_as_formula(formula)
automata_size = 1
for clause in cnf.args():
    automata_size *= len(clause.get_free_variables())

print(f"autoamta size: {automata_size}")
