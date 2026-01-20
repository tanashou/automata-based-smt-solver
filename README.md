# Automata-Based Presburger Arithmetic SMT Solver (AbSMT)

This is an SMT solver for **Presburger Arithmetic** (Linear Integer Arithmetic) based on automata theory.
It utilizes the [Spot](https://spot.lre.epita.fr/) library for efficient automata manipulation.

## Features & Limitations

### ✅ What it can do
- **Decidability Check:** Determines `sat` (satisfiable) or `unsat` (unsatisfiable) for given logical formulas.
- **Problem Domains:**
  - **LIA (Linear Integer Arithmetic):** Handles formulas with quantifiers (e.g., $\forall$, $\exists$).
    - *Note: Supports pure integer arithmetic only (standard Presburger Arithmetic).*
  - **QF_LIA (Quantifier-Free Linear Integer Arithmetic):** Capable of solving simple quantifier-free instances.

### ❌ What it cannot do (Current Limitations)
- **Boolean Variables:** It **does not** support formulas containing Boolean variables (e.g., `(declare-fun b () Bool)`). Only Integer variables (`Int`) are supported.
- **Model Generation:** Currently, it only outputs the satisfiability result (`sat`/`unsat`) and **does not** generate a specific assignment (model) for variables.

## Setup

You can set up the environment using either **VSCode Dev Container** (recommended) or by building the **Docker image** manually.

### Option 1: VSCode Dev Container (Recommended)
Simply open this project in **VSCode**. The environment will be automatically configured.

- **Project root:** `/workspaces/SMT-Solver`

### Option 2: Build with Docker
To match the host user permissions, build the docker image with the following command:

```bash
docker build \
  --build-arg USER_UID=$(id -u) \
  --build-arg USER_GID=$(id -g) \
  -t absmt:latest .
```

Start the container and access the shell:

```
docker run -it --rm -v $(pwd):/app absmt:latest
```

## Usage

### 1. Running Examples
We provide an example script `example.py` to demonstrate how to use the solver API and load SMT-LIB files.

```bash
python example.py
```

This script demonstrates:

-  Constructing a formula (Frobenius Coin Problem) using PySMT API.

-  Parsing and solving a formula from an SMT-LIB string.

-  Loading and checking an SMT-LIB file (.smt2).
### 2. Benchmark test
A utility script `run_bench.py` is available to automate solver benchmarking. It runs tests on a specified directory, handles timeouts, and exports the results to CSV.

Benchmark files are collected from here:
- [QF_LIA Benchmarks Download Link](https://zenodo.org/records/16740866/files/QF_LIA.tar.zst?download=1)
- [LIA Benchmarks Download Link](https://zenodo.org/records/16740866/files/LIA.tar.zst?download=1)

For detailed information about the datasets, please refer to [benchmarks/README.md](./benchmarks/README.md).

#### Command
```bash
python run_bench.py <TARGET> [--time <SECONDS>] [--mem-limit <MEMORY_LIMIT>]
```
| Option        | Required |      Default      | Description                                                                          |
| :------------ | :------: | :---------------: | :----------------------------------------------------------------------------------- |
| `TARGET`      | **Yes**  |         -         | Path to the benchmark directory OR a specific file (e.g., benchmarks/ or test.smt2). |
| `--time`      |    No    |       `60`        | Maximum execution time per test in seconds.                                          |
| `--mem-limit` |    No    | Auto (80% of RAM) | Memory limit for each test (e.g., '8GB', '4000MB').                                  |

#### Output
Results (JSON and CSV) are automatically saved in the `benchmark_result/` directory. Files are named based on the target directory and the current timestamp to avoid overwrites.

Naming Format: <Directory_Name>_result_<YYYYMMDD_HHMMSS>.csv

Example: If you run `python run_bench.py ./benchmarks/LIA/tptp`, the output will be: `./benchmark_result/LIA_tptp_result_20251223_153000.csv`
## License
This project is licensed under the GNU General Public License v3.0 (GPLv3).

Some files in this repository are derived from third-party projects licensed under the MIT License. All such files retain their original copyright and license notices, as required.

### Use of Spot
This project uses the [Spot](https://spot.lre.epita.fr/) library, which is distributed under the GNU GPL v3 license.
Because Spot is a dependency, the terms of the GPL v3 also apply to this project.
