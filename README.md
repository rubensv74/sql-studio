# SQL Studio

SQL Studio is a Python 3.12+ toolkit for static analysis of SQL repositories.

**Current version:** `0.12.0`  
**Development status:** stabilized MVP core; next functional milestone is Circular Dependency Detection.

## Implemented capabilities

- repository scanning and JSON repository model;
- T-SQL tokenization and parsing;
- SQL object, parameter, variable and reference extraction;
- directed dependency graph;
- dependency serialization;
- cross-reference analysis;
- transitive impact analysis;
- JSON and self-contained HTML impact reports;
- command-line interface;
- automated validation in GitHub Actions.

## Dependency and impact semantics

The dependency graph stores edges as:

```text
source -> target
```

meaning that `source` depends on `target`.

Therefore:

- `dependencies_of(A)` answers **what A uses**;
- `dependents_of(A)` answers **what uses A**;
- Impact Analysis follows `dependents_of()` transitively to answer **what can be affected if A changes**.

This distinction is part of the public architecture contract and is covered by tests.

## Quick start

No installation step is currently required when running from the repository root.

```bash
python cli/sqlstudio.py --help
python cli/sqlstudio.py parse examples/sample_procedure.sql
python cli/sqlstudio.py dependencies examples/sample_procedure.sql
python cli/sqlstudio.py cross-references examples/sample_procedure.sql
python cli/sqlstudio.py impact sys.objects examples/sample_procedure.sql
python cli/sqlstudio.py impact sys.objects examples/sample_procedure.sql --html reports/impact.html
```

## Validation

Run the complete test suite from the repository root:

```bash
PYTHONPATH=src python -m unittest discover -s tests -p "test_*.py" -v
```

GitHub Actions also validates:

- Python 3.12;
- bytecode compilation;
- package imports;
- the complete unit-test suite;
- CLI help and smoke commands.

## Repository layout

```text
src/sqlstudio/              Production Python package
  parser/                   SQL tokenizer and parser
  dependencies/             Dependency graph and resolver
  cross_reference/          Incoming/outgoing cross references
  impact_analysis/          Change-impact traversal and reporting
cli/sqlstudio.py            Repository-local CLI
tests/                      Automated tests
docs/                       Architecture, CLI and functional contracts
examples/                   Reproducible SQL examples
```

Legacy or experimental areas such as benchmark/profiler are not considered completed MVP capabilities until their behavior is implemented and tested.

## Documentation

- [Architecture](docs/architecture.md)
- [CLI](docs/CLI.md)
- [Impact Report contract](docs/impact-report.md)
- [Roadmap](docs/roadmap.md)
- [Development audit](docs/development-audit.md)
- [AI development rules](AI_DEVELOPMENT.md)

## Development rule

Git is the source of truth. Functional changes require tests, reproducible validation and Conventional Commits. See `AI_DEVELOPMENT.md` for the repository working agreement.
