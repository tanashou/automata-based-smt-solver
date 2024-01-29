import pytest
from my_smt_solver import PresburgerArithmetic, Relation

class TestPresburgerArithmetic:
    def test_flip_ineq(self) -> None:
        p1 = PresburgerArithmetic([(2, "x"), (-3, "z")], Relation.LEQ, -2)
        p2 = PresburgerArithmetic([(2, "x"), (-3, "z")], Relation.EQ, -2)

        p1.flip_ineq()
        assert p1.relation == Relation.GEQ
        assert p1.terms == [(-2, "x"), (3, "z")]
        assert p1.const == 2

        with pytest.raises(ValueError):
            p2.flip_ineq()

    def test_const(self) -> None:
        p = PresburgerArithmetic([(2, "x"), (-3, "z")], Relation.LEQ, -2)
        p.const += 1
        assert p.const == -1

