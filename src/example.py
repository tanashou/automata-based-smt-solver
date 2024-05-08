from my_smt_solver import Solver, PresburgerArithmetic, Relation


p1 = PresburgerArithmetic(
    terms=[(1, "x"), (-1, "y")],
    relation=Relation.EQ,
    const=2,
)

p2 = PresburgerArithmetic(
    terms=[(1, "x")],
    relation=Relation.GEQ,
    const=2,
)

print(p1)
print(p2)


s = Solver()
s.add(p1)
s.add(p2)

s.check()
