from my_smt_solver.presburger_arithmetic import PresburgerArithmetic, Relation
from my_smt_solver.solver import Solver

p1 = PresburgerArithmetic(
    terms=[(1230, "x1"), (-1, "x2")],
    relation=Relation.LEQ,
    const=0,
)

p2 = PresburgerArithmetic(
    terms=[(1999, "x2"), (-1, "x3")],
    relation=Relation.LEQ,
    const=0,
)

p3 = PresburgerArithmetic(
    terms=[(8000, "x3"), (-1, "x4")],
    relation=Relation.LEQ,
    const=0,
)

p4 = PresburgerArithmetic(
    terms=[(1, "x1")],
    relation=Relation.GEQ,
    const=1002,
)

p5 = PresburgerArithmetic(
    terms=[(-2, "x5"), (-1, "x6")],
    relation=Relation.LEQ,
    const=0,
)

p6 = PresburgerArithmetic(
    terms=[(1, "x5"), (4000, "x4")],
    relation=Relation.LEQ,
    const=0,
)

p7 = PresburgerArithmetic(
    terms=[(1, "x6")],
    relation=Relation.LT,
    const=0,
)

print(p1)
print(p2)
print(p3)
print(p5)
print(p6)
print(p7)


s = Solver()
s.add(p1)
s.add(p2)
s.add(p3)
s.add(p5)
s.add(p6)
s.add(p7)


s.check()
