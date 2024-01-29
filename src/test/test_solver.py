import pytest
from my_smt_solver import Solver, PresburgerArithmetic, Relation


# Define a fixture for creating NFAs with common structure
@pytest.fixture
def sample_prb_arithmetics() -> list[PresburgerArithmetic]:
    return [
        PresburgerArithmetic(
            terms=[(2, "x"), (-3, "z")],
            relation=Relation.EQ,
            const=2,
        ),
        PresburgerArithmetic(
            terms=[(1, "x")],
            relation=Relation.GEQ,
            const=0,
        ),
        PresburgerArithmetic(
            terms=[(100, "x"), (-19, "y")],
            relation=Relation.NEQ,
            const=0,
        ),
    ]


@pytest.fixture
def sample_prb_arithmetics2() -> list[PresburgerArithmetic]:
    return [
        PresburgerArithmetic(
            terms=[(2, "x"), (-3, "z")],
            relation=Relation.EQ,
            const=2,
        ),
        PresburgerArithmetic(
            terms=[(100, "x"), (-19, "y")],
            relation=Relation.NEQ,
            const=0,
        ),
    ]


@pytest.fixture
def sample_prb_arithmetics3() -> list[PresburgerArithmetic]:
    return [
        PresburgerArithmetic(
            terms=[(1, "x")],
            relation=Relation.LEQ,
            const=4,
        ),
    ]

@pytest.fixture
def sample_prb_arithmetics4() -> list[PresburgerArithmetic]:
    return [
        PresburgerArithmetic(
            terms=[(1, "x"), (1, "y")],
            relation=Relation.LT,
            const=0,
        ),
        PresburgerArithmetic(
            terms=[(1, "y"), (1, "z")],
            relation=Relation.GT,
            const=4,
        ),
        PresburgerArithmetic(
            terms=[(1, "z"), (1, "w")],
            relation=Relation.GEQ,
            const=4,
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

def test_check2(sample_prb_arithmetics4: list[PresburgerArithmetic]) -> None:
    s = Solver()
    for prb_arithmetic in sample_prb_arithmetics4:
        s.add(prb_arithmetic)

    result = s.check()
    assert s.variables == ["w", "x", "y", "z"]
    for prb_arithmetic in sample_prb_arithmetics4:
        assert prb_arithmetic.is_valid_expression(result)

def test_leq(sample_prb_arithmetics3: list[PresburgerArithmetic]) -> None:
    s = Solver()
    for prb_arithmetic in sample_prb_arithmetics3:
        s.add(prb_arithmetic)

    result = s.check()
    assert s.variables == ["x"]
    assert sorted(s.coefs) == sorted([[1]])
    for prb_arithmetic in sample_prb_arithmetics3:
        assert prb_arithmetic.is_valid_expression(result)


