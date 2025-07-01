# ruff: noqa: I001, ANN201, LOG015, G004
from automata_based_smt_solver.formula.smtlib_reader import SMTLIBReader
from automata_based_smt_solver.solver import Solver

import logging

logging.basicConfig(
    level=logging.DEBUG,  # DEBUGレベル以上のログをすべて出力する
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),  # コンソールに出力
    ],
)

prime_cone_2 = """
(set-info :smt-lib-version 2.6)
(set-logic QF_LIA)
(set-info :category "crafted")
(set-info :status sat)
(declare-fun x_0 () Int)
(declare-fun x_1 () Int)
(assert (>= x_0 0))
(assert (>= x_1 0))
(assert (<= (+ (* (- 4) x_0) (* 2 x_1)) 0))
(assert (<= (+ (* 3 x_0) (* (- 3) x_1)) 0))
(assert (>= (+ x_0 x_1) 1))
(check-sat)
(exit)
"""
# from prime_cone
prime_cone_3 = """
(set-info :smt-lib-version 2.6)
(set-logic QF_LIA)
(set-info :category "crafted")
(set-info :status sat)
(declare-fun x_0 () Int)
(declare-fun x_1 () Int)
(declare-fun x_2 () Int)
(assert (>= x_0 0))
(assert (>= x_1 0))
(assert (>= x_2 0))
(assert (<= (+ (* (- 9) x_0) (* 2 x_1) (* 2 x_2)) 0))
(assert (<= (+ (* 3 x_0) (* (- 8) x_1) (* 3 x_2)) 0))
(assert (<= (+ (* 5 x_0) (* 5 x_1) (* (- 6) x_2)) 0))
(assert (>= (+ x_0 x_1 x_2) 1))
(check-sat)
(exit)
"""

prime_cone_4 = """
(set-info :smt-lib-version 2.6)
(set-logic QF_LIA)
(set-info :category "crafted")
(set-info :status sat)
(declare-fun x_0 () Int)
(declare-fun x_1 () Int)
(declare-fun x_2 () Int)
(declare-fun x_3 () Int)
(assert (>= x_0 0))
(assert (>= x_1 0))
(assert (>= x_2 0))
(assert (>= x_3 0))
(assert (<= (+ (* (- 16) x_0) (* 2 x_1) (* 2 x_2) (* 2 x_3)) 0))
(assert (<= (+ (* 3 x_0) (* (- 15) x_1) (* 3 x_2) (* 3 x_3)) 0))
(assert (<= (+ (* 5 x_0) (* 5 x_1) (* (- 13) x_2) (* 5 x_3)) 0))
(assert (<= (+ (* 7 x_0) (* 7 x_1) (* 7 x_2) (* (- 11) x_3)) 0))
(assert (>= (+ x_0 x_1 x_2 x_3) 1))
(check-sat)
(exit)
"""


def main():
    reader = SMTLIBReader()
    solver = Solver()
    status, formula = reader.from_smt_lib(prime_cone_2)
    logging.info(f"Start solving formula. Expected status: {status}")
    logging.debug(f"Input formula: {formula}")

    solver.add(formula)
    result = solver.solve_with_dnf()
    logging.info(f"Finish solving formula. Result: {result}, Expected: {status}")


if __name__ == "__main__":
    main()
