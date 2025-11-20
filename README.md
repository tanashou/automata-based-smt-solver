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
docker run -it -v $(pwd)/benchmarks/QF_LIA:/app/benchmarks/QF_LIA absmt:latest /bin/bash
```

### Benchmark test
Benchmark files can be found in https://zenodo.org/records/16740866/files/QF_LIA.tar.zst?download=1

Download and extract the files to `benchmarks/`.
```bash
pytest --benchmark-only --benchmark-group-by=param:path
```
Add `-rA` option to see the peak memory usage.
```bash
pytest --benchmark-only --benchmark-group-by=param:path -rA
```

## License
This project is licensed under the GNU General Public License v3.0 (GPLv3).

Some files in this repository are derived from third-party projects licensed under the MIT License. All such files retain their original copyright and license notices, as required.

### Use of Spot
This project uses the [Spot](https://spot.lre.epita.fr/) library, which is distributed under the GNU GPL v3 license.
Because Spot is a dependency, the terms of the GPL v3 also apply to this project.
