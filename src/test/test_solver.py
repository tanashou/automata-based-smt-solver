import pytest
from src.my_smt_solver import Solver
from src.my_smt_solver import PresburgerArithmetic
from src.my_smt_solver import Relation


# Define a fixture for creating NFAs with common structure
@pytest.fixture
def sample_solver() -> Solver:
    prb1 = PresburgerArithmetic(
        terms=[("x", 1), ("z", 1)],
        relation=Relation.EQ,
        const=2,
    )

    prb2 = PresburgerArithmetic(
        terms=[("x", 1)],
        relation=Relation.GEQ,
        const=0,
    )

    prb3 = PresburgerArithmetic(
        terms=[("x", 1), ("y", 1)],
        relation=Relation.NEQ,
        const=0,
    )

    solver = Solver()
    solver.add(prb1)
    solver.add(prb2)
    solver.add(prb3)
    return solver


def test_set_variables(sample_solver: Solver) -> None:
    """
    x + z = 2 and x >= 0
    """
    s = sample_solver

    s.set_variables()

    assert s.variables == ["x", "y", "z"]
