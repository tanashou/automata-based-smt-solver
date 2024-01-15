from my_smt_solver import Solver, PresburgerArithmetic, Relation


p1 = PresburgerArithmetic(
    terms=[(2, "x"), (-3, "z")],
    relation=Relation.EQ,
    const=2,
)

p2 = PresburgerArithmetic(
    terms=[(100, "x"), (-19, "y")],
    relation=Relation.NEQ,
    const=0,
)

print(p1)
print(p2)

s = Solver()
s.add(p1)
s.add(p2)

s.check()
