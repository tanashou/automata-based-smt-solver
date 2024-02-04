from my_smt_solver import Solver, PresburgerArithmetic, Relation


p1 = PresburgerArithmetic(
    terms=[(1, "x"), (-1, "y")],
    relation=Relation.EQ,
    const=2,
)

p2 = PresburgerArithmetic(
    terms=[(2, "x"), (1, "z")],
    relation=Relation.LEQ,
    const=5,
)

p3 = PresburgerArithmetic(
    terms=[(1, "y"), (3, "z")],
    relation=Relation.NEQ,
    const=0,
)

print(p1)
print(p2)
print(p3)

s = Solver()
s.add(p1)
s.add(p2)
s.add(p3)

s.check()
