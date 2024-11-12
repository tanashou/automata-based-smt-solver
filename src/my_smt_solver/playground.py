from pysmt.rewritings import CNFizer
from pysmt.shortcuts import (
    GE,
    LE,
    And,
    Equals,
    Int,
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
    Equals(z, Plus(x, Times(Int(-1), y))),  # z = x - y
    Or(
        LE(z, Int(-5)),  # z <= -5
        GE(z, Int(5)),  # z >= 5
    ),
)

# Print the original formula
print("Original formula:")
print(formula)

# Create a CNFizer instance
cnfizer = CNFizer()

# Convert the formula to CNF
cnf = cnfizer.convert(formula)

# Print the CNF formula
print("\nCNF formula:")
print(cnf)

# Print individual clauses
print("\nIndividual clauses:")
for clause in cnf:
    print(clause)
