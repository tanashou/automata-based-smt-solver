## Benchmarks

The benchmarks in this repository were obtained from [SMT-LIB Release 2025 (non-incremental benchmarks)](https://zenodo.org/records/16740866), specifically from the **LIA** (Linear Integer Arithmetic) and **QF_LIA** (Quantifier-Free LIA) categories.
Official Site: [http://smt-lib.org/](http://smt-lib.org/)

The primary purpose of this tool (`absmt`) is to solve **Quantified Presburger Arithmetic (LIA)** and verify automata operations. Therefore, experimental data was selected based on the following criteria:

### 1. LIA Category (Main Target)
For the LIA dataset, we adopted as many instances as possible that do not fall under the "Common Exclusion Criteria" described below.

**[Special Notes on LIA Benchmarks]**
Although the total number of benchmarks in the LIA category is limited, specific benchmark families were excluded based on the tool's current specification (lack of support for Boolean variables) as follows:

* **Totally Excluded Families:**
    * `psyco`: Excluded from this experiment because all instances contain Boolean variable definitions.
* **Partially Excluded Families:**
    * `UltimateAutomizer`: Only the following **5 instances** contain Boolean variable definitions, so they were excluded:
        * `Primes_true-unreach-call.c_127.smt2`
        * `Primes_true-unreach-call.c_187.smt2`
        * `Primes_true-unreach-call.c_673.smt2`
        * `Primes_true-unreach-call.c_678.smt2`
        * `Primes_true-unreach-call.c_798.smt2`

### 2. QF_LIA Category (Baseline Check)
Since the QF_LIA category is extremely large, a subset was extracted based on the following criteria for the purpose of basic operational verification (sanity check) of the tool:

* **File Size:** Relatively small instances (e.g., `[XX]` KB or less).
* **Structure:** Selected from families with basic logical structures.

---

### Common Exclusion Criteria
To align with the current specifications and implementation status of `absmt`, files meeting the following conditions have been excluded from the experiment:

* **Instances containing Boolean variable declarations:**
    * The current version supports only pure integer variables. Handling formulas with mixed Boolean variables (`Bool` sort) and integer variables is excluded as the **theoretical formulation and implementation are currently under consideration (Future Work)**.
* **Instances containing incremental descriptions:**
    * Files containing multiple `check-sat` commands within a single file. Currently, only **Non-incremental** execution is supported.

### License
The benchmarks are distributed under the [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/).
