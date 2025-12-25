# Automata-Based Presburger Arithmetic SMT Solver

This is a SMT solver for Presburger arithmetic (or linear integer arithmetic) based on automata.

This project is in progress.

## Installation
open this project in Dev Container using VSCode.

## Usage
### Using in devcontainer
project root: `/workspaces/SMT-Solver`
```bash
conda activate absmt
...
```

### Build with Docker
To match the host user permissions, build the docker image with the following command:
```bash
docker build \
  --build-arg USER_UID=$(id -u) \
  --build-arg USER_GID=$(id -g) \
  -t absmt:latest .
```
Getting in the bash
```
docker run -it --rm -v $(pwd):/app absmt:latest
```

### Benchmark test
Benchmark files can be found in https://zenodo.org/records/16740866/files/QF_LIA.tar.zst?download=1, https://zenodo.org/records/16740866/files/LIA.tar.zst?download=1

A utility script to automate solver benchmarking. It runs tests on a specified directory, handles timeouts, and exports the results to CSV.
```bash
python run_bench.py --dir <TARGET_DIR> [--time <SECONDS>]
```
| Option   | Required | Default | Description                                                       |
| :------- | :------: | :-----: | :---------------------------------------------------------------- |
| `--dir`  | **Yes**  |    -    | Path to the directory containing benchmark files (e.g., `.smt2`). |
| `--time` |    No    |  `60`   | Maximum execution time per test in seconds.                       |

#### Output
Results (JSON and CSV) are automatically saved in the `benchmark_result/` directory. Files are named based on the target directory and the current timestamp to avoid overwrites.

Naming Format: <Directory_Name>_result_<YYYYMMDD_HHMMSS>.csv

Example: If you run `python run_bench.py --dir ./benchmarks/LIA/tptp`, the output will be: `./benchmark_result/LIA_tptp_result_20251223_153000.csv`
## License
This project is licensed under the GNU General Public License v3.0 (GPLv3).

Some files in this repository are derived from third-party projects licensed under the MIT License. All such files retain their original copyright and license notices, as required.

### Use of Spot
This project uses the [Spot](https://spot.lre.epita.fr/) library, which is distributed under the GNU GPL v3 license.
Because Spot is a dependency, the terms of the GPL v3 also apply to this project.
