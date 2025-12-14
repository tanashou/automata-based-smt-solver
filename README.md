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
```
docker build -t absmt:latest .
```
Getting in the bash
```
docker run -it -v $(pwd):/app absmt:latest /bin/bash
conda activate absmt
```

### Benchmark test
Benchmark files can be found in https://zenodo.org/records/16740866/files/QF_LIA.tar.zst?download=1, https://zenodo.org/records/16740866/files/LIA.tar.zst?download=1

Download and extract the files to `benchmarks/`.
Timeout and max rounds can be adjusted as needed (default: timeout=120, max_rounds=10).
Use `benchmark-autosave` to save benchmark results in json formuat in `./.benchmarks/Linux-CPython-3.12-64bit/`.
```bash
pytest tests/test_solver_benchmark_cli.py \
  --benchmark-timeout=120 \
  --benchmark-max-rounds=10 \
  --benchmark-dir ./benchmarks/LIA/<EXAMPLE_DIR>/
  --benchmark-autosave
```
If you want to convert the result to CSV format, use the following command:
```bash
pytest-benchmark compare ./.benchmarks/Linux-CPython-3.12-64bit/<FILENAME>.json --csv ./.benchmarks/Linux-CPython-3.12-64bit/<FILENAME>.csv
```

## License
This project is licensed under the GNU General Public License v3.0 (GPLv3).

Some files in this repository are derived from third-party projects licensed under the MIT License. All such files retain their original copyright and license notices, as required.

### Use of Spot
This project uses the [Spot](https://spot.lre.epita.fr/) library, which is distributed under the GNU GPL v3 license.
Because Spot is a dependency, the terms of the GPL v3 also apply to this project.
