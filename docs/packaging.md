# Packaging and Installation Contract

## Purpose

SQL Studio is distributed as a standard Python 3.12+ package using a `src/` layout and PEP 517 build metadata in `pyproject.toml`.

This milestone makes the project buildable and installable. It does not publish SQL Studio to PyPI or define release/tag automation.

## Distribution identity

Three names have distinct roles:

- distribution name: `sql-studio`;
- import package: `sqlstudio`;
- console command: `sqlstudio`.

The console entry point is declared as:

```toml
[project.scripts]
sqlstudio = "sqlstudio.cli:main"
```

## Build backend

The project uses setuptools through the standard PEP 517 interface:

```toml
[build-system]
requires = ["setuptools>=77", "wheel"]
build-backend = "setuptools.build_meta"
```

Production packages are discovered only under `src/`.

## Version contract

The canonical runtime/package version is:

```text
src/sqlstudio/_version.py -> sqlstudio.__version__
```

`pyproject.toml` reads that value dynamically. `core/version.txt` is retained as a compatibility mirror and automated tests require it to match the package version.

The CLI exposes the same value through:

```bash
sqlstudio --version
```

## Build

Install the build frontend and create both distribution formats:

```bash
python -m pip install build
python -m build
```

For version `0.16.0`, expected artifacts are:

```text
dist/sql_studio-0.16.0.tar.gz
dist/sql_studio-0.16.0-py3-none-any.whl
```

The wheel is platform-independent because SQL Studio currently has no compiled extension modules.

## Installation

Install directly from a checkout:

```bash
python -m pip install .
```

Install a generated wheel:

```bash
python -m pip install dist/sql_studio-0.16.0-py3-none-any.whl
```

Install in editable development mode:

```bash
python -m pip install -e .
```

## CLI compatibility

`src/sqlstudio/cli.py` is the canonical CLI implementation.

`cli/sqlstudio.py` exists only for backward-compatible execution from a repository checkout. It bootstraps `src/` and reexports canonical CLI callables so existing tests and direct Python consumers do not break.

New automation should prefer the installed `sqlstudio` command.

## License

Package metadata declares the MIT license and includes the complete repository `LICENSE` text in distributions.

## CI gate

A packaging change is not complete merely because source-based tests pass. GitHub Actions must:

1. run the existing compile/import/unit/CLI-wrapper gates;
2. build both sdist and wheel;
3. verify the expected versioned artifact names;
4. install the wheel;
5. change the working directory outside the repository checkout;
6. clear `PYTHONPATH`;
7. verify package metadata and `sqlstudio --version`;
8. run a real installed-CLI static analysis;
9. upload the built distributions as workflow artifacts.

This prevents false positives where the console command accidentally imports `src/sqlstudio` from the repository rather than the installed wheel.

## Publication boundary

No PyPI credentials, publication workflow or automatic GitHub Release is introduced by this contract. Publication requires a separate release-policy decision, including version/tag ownership and release gates.
