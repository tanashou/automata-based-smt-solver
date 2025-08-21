Suggested development commands for this project

- Create and activate conda env (from repo root):
  conda env create -f environment.yml
  conda activate absmt

- Install Python deps (if not using conda for everything):
  pip install -e .[dev]

- Run tests:
  pytest -q

- Run lint (ruff):
  ruff check src tests

- Type check (pyright):
  pyright

- Formatting / pre-commit:
  pre-commit run --all-files

- Run individual scripts (examples located in `src/performance_test`)
