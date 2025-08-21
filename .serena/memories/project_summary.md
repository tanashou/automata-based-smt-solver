Automata-Based Presburger Arithmetic SMT Solver

Purpose:
- Implements an SMT solver for Presburger arithmetic (linear integer arithmetic) based on automata.

Tech stack:
- Python >= 3.11 (environment.yml requests 3.12)
- Conda environment named `absmt` with `spot` library
- Python dependencies: `pysmt==0.9.6` (declared in pyproject.toml)
- Dev tools: pytest, ruff, pyright, pre-commit

Code structure:
- `src/absmt`: core package (solver, automata builder, formula automata builder, types, etc.)
- `src/absmt/automata`: automata implementations (nfa, spot integration, msbf alphabet)
- `src/absmt/formula`: formula parsing, normalizers, rewritings
- `src/performance_test`: performance helpers and scripts
- `tests`: unit tests covering many modules

Development commands:
- Tests: `pytest` (project uses pytest)
- Linting: `ruff` (ruff.toml is present)
- Type checking: `pyright` (pyrightconfig.json present)

Notes:
- Some files reference the Spot library which is GPLv3; project uses GPLv3 overall.
- README.md contains minimal usage instructions; dev container recommended for setup.
