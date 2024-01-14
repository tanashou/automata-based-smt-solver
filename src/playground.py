from my_smt_solver import Solver, PresburgerArithmetic, Relation


p1 = PresburgerArithmetic(
    terms=[("x", 2), ("z", -3)],
    relation=Relation.EQ,
    const=2,
)

p2 = PresburgerArithmetic(
    terms=[("x", 100), ("y", -19)],
    relation=Relation.NEQ,
    const=0,
)

s = Solver()
s.add(p1)
s.add(p2)

s.check()
s.check()
s.check()
