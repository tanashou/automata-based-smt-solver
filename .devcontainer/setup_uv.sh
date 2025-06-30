uv pip sync pyproject.toml
# fixes ModuleNotFoundError: No module named '_distutils_hack' in python >3.12
uv pip install setuptools
uv pip install --group dev-dependencies -r pyproject.toml
# pyproject.toml don't support editable installs in env not managed by uv.
uv pip install -e .
pre-commit install
