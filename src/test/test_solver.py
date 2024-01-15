import pytest
from my_smt_solver import Solver, PresburgerArithmetic, Relation


# Define a fixture for creating NFAs with common structure
@pytest.fixture
def sample_prb_arithmetics() -> list[PresburgerArithmetic]:
    return [
        PresburgerArithmetic(
            terms=[("x", 2), ("z", -3)],
            relation=Relation.EQ,
            const=2,
        ),
        PresburgerArithmetic(
            terms=[("x", 1)],
            relation=Relation.GEQ,
            const=0,
        ),
        PresburgerArithmetic(
            terms=[("x", 100), ("y", -19)],
            relation=Relation.NEQ,
            const=0,
        ),
    ]


@pytest.fixture
def sample_prb_arithmetics2() -> list[PresburgerArithmetic]:
    return [
        PresburgerArithmetic(
            terms=[("x", 2), ("z", -3)],
            relation=Relation.EQ,
            const=2,
        ),
        PresburgerArithmetic(
            terms=[("x", 100), ("y", -19)],
            relation=Relation.NEQ,
            const=0,
        ),
    ]


def test_check(sample_prb_arithmetics2: list[PresburgerArithmetic]) -> None:
    s = Solver()
    for prb_arithmetic in sample_prb_arithmetics2:
        s.add(prb_arithmetic)

    result = s.check()
    assert s.variables == ["x", "y", "z", "z_neq"]
    assert sorted(s.coefs) == sorted([[2, 0, -3, 0], [100, -19, 0, 1], [0, 0, 0, 1]])
    for prb_arithmetic in sample_prb_arithmetics2:
        assert prb_arithmetic.is_valid_expression(result)
