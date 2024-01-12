import pytest
from src.my_smt_solver import Solver
from src.my_smt_solver import PresburgerArithmetic
from src.my_smt_solver import Relation


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


def test_set_variables(sample_prb_arithmetics: list[PresburgerArithmetic]) -> None:
    s = Solver()
    for prb_arithmetic in sample_prb_arithmetics:
        s.add(prb_arithmetic)

    s.set_variables()

    assert s.variables == ["x", "y", "z"]


def test_set_coefs(sample_prb_arithmetics: list[PresburgerArithmetic]) -> None:
    s = Solver()
    for prb_arithmetic in sample_prb_arithmetics:
        s.add(prb_arithmetic)

    s.set_variables()
    s.set_coefs()

    assert s.coefs == [[2, 0, -3], [1, 0, 0], [100, -19, 0]]

def test_update_coefs_for_neq(sample_prb_arithmetics: list[PresburgerArithmetic]) -> None:
    s = Solver()
    for prb_arithmetic in sample_prb_arithmetics:
        s.add(prb_arithmetic)

    s.set_variables()
    s.set_coefs()
    s.update_coefs_for_neq()

    assert s.variables == ["x", "y", "z", "z_neq"]
    assert s.coefs == [[2, 0, -3, 0], [1, 0, 0, 0], [100, -19, 0, 1]]