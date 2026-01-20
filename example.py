import textwrap

from pysmt.shortcuts import GE, And, Equals, Exists, Int, Plus, Symbol, Times
from pysmt.typing import INT

from absmt.solver import Solver


def run_frobenius_example():
    """Example 1: Constructing a formula directly using the PySMT API."""
    print("\n" + "=" * 60)
    print("Example 1: Frobenius Coin Problem via PySMT API")
    print("=" * 60)

    # Definition of the formula: ∃a ∃b . (a >= 0 ∧ b >= 0 ∧ x = 3a + 5b)
    # Defines number x representable as a linear combination of 3 and 5.
    x = Symbol("x", INT)
    a = Symbol("a", INT)
    b = Symbol("b", INT)

    formula = Exists(
        [a, b],
        And(
            GE(a, Int(0)),
            GE(b, Int(0)),
            Equals(x, Plus(Times(Int(3), a), Times(Int(5), b))),
        ),
    )

    print("Formula constructed via PySMT.")

    # Initialize and run the solver
    solver = Solver()
    solver.add(formula)

    # Solve the formula
    result = solver.solve()
    print(f"Solver result: {result}")


def run_smtlib_string_example():
    """Example 2: Reading and solving a string in SMT-LIB format."""
    print("\n" + "=" * 60)
    print("Example 2: SMT-LIB String Parsing")
    print("=" * 60)

    # Problem derived from the TPTP Library (status: unsat).
    # Does there exist a z such that (x + z = y) holds for all x, y? -> Does not exist.
    smt2_str = textwrap.dedent("""
    (set-info :smt-lib-version 2.6)
    (set-logic LIA)
    (set-info :category "industrial")
    (set-info :status unsat)
    (assert (not (forall ((?U Int) (?V Int)) (exists ((?W Int)) (= (+ ?U ?W) ?V)))))
    (check-sat)
    (exit)
    """)

    solver = Solver()

    print("Parsing SMT-LIB string...")
    expected_status = solver.read_from_smtlib(smt2_str)
    print(f"Expected status from metadata: {expected_status}")

    result = solver.solve()
    print(f"Solver result: {result}")

    if result != expected_status:
        print(f"Warning: Result does not match expected status '{expected_status}'.")
    else:
        print("Verification successful: Result matches expected status.")


def run_smtlib_file_example():
    """Example 3: Reading and solving an SMT-LIB file (.smt2)."""
    print("\n" + "=" * 60)
    print("Example 3: SMT-LIB File Loading")
    print("=" * 60)

    # Same problem as in Example 2, but loaded from a file.
    smt2_path_str = "benchmarks/LIA/tptp/NUM915=1.smt2"

    solver = Solver()

    # Example usage of the is_file_path=True option
    try:
        print(f"Loading file: {smt2_path_str}")
        expected_status = solver.read_from_smtlib(smt2_path_str, is_file_path=True)
        print(f"Expected status from metadata: {expected_status}")

        result = solver.solve()
        print(f"Solver result: {result}")

        if result != expected_status:
            print(
                f"Warning: Result does not match expected status '{expected_status}'."
            )
        else:
            print("Verification successful: Result matches expected status.")

    except Exception as e:
        print(f"Error processing file: {e}")


if __name__ == "__main__":
    run_frobenius_example()
    run_smtlib_string_example()
    run_smtlib_file_example()
