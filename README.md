# SQL Studio

SQL Studio is a Python 3.12+ toolkit for static analysis of SQL repositories.

**Current version:** `0.15.0`  
**Development status:** stabilized MVP static-analysis core with consolidated Rule Engine; next milestone is Packaging and installable CLI.

## Implemented capabilities

- repository scanning and JSON repository model;
- T-SQL tokenization and parsing;
- SQL object, parameter, variable and reference extraction;
- directed dependency graph;
- dependency serialization;
- cross-reference analysis;
- transitive impact analysis;
- circular dependency detection using strongly connected components;
- conservative dead-object candidate detection;
- consolidated static-analysis Rule Engine with normalized severities/findings;
- CI quality gates through `analyze --fail-on`;
- JSON and self-contained HTML impact reports;
- command-line interface;
- automated validation in GitHub Actions.

## Dependency semantics

The dependency graph stores edges as:

```text
source -> target
```

meaning that `source` depends on `target`.

Therefore:

- `dependencies_of(A)` answers **what A uses**;
- `dependents_of(A)` answers **what uses A**;
- Impact Analysis walks `dependents_of()` transitively;
- Circular Dependency Detection reports strongly connected components;
- Dead Object Detection reviews components with no incoming static references from outside the component.

## Rule Engine

Structural services such as Dependency, Cross Reference and Impact remain independent APIs. Actionable detections are consolidated through `StaticAnalysisRuleEngine`.

Built-in rules:

- `SQL001` — Circular dependency — `error`;
- `SQL002` — Dead object candidate — `warning`.

`StaticAnalysisAnalyzer` parses each SQL input once, builds one dependency graph and shares that context across all selected rules. Existing dedicated analyzers/commands remain supported.

## Dead-object safety contract

Dead Object Detection produces **candidates only**. It never asserts that an object is safe to delete.

A candidate can still be used by application code, SQL Agent jobs, ETL/orchestration, reporting tools, external databases, permissions-driven workflows or dynamic SQL that is not statically resolvable. Known externally invoked SQL objects can be supplied with repeatable `--entry-point` arguments. Triggers are excluded by default because their invocation is implicit.

## Quick start

```bash
python cli/sqlstudio.py --help
python cli/sqlstudio.py parse examples/sample_procedure.sql
python cli/sqlstudio.py dependencies examples/sample_procedure.sql
python cli/sqlstudio.py cross-references examples/sample_procedure.sql
python cli/sqlstudio.py impact sys.objects examples/sample_procedure.sql
python cli/sqlstudio.py circular-dependencies examples/circular_dependencies
python cli/sqlstudio.py dead-objects examples/dead_objects --entry-point dbo.Entry
python cli/sqlstudio.py analyze examples/dead_objects --entry-point dbo.Entry
python cli/sqlstudio.py analyze examples/circular_dependencies --rule SQL001 --fail-on error
```

`analyze --fail-on` returns exit code `2` when the configured finding threshold is reached. Exit code `1` remains reserved for handled execution/input failures.

## Validation

```bash
PYTHONPATH=src python -m unittest discover -s tests -p "test_*.py" -v
```

GitHub Actions validates Python 3.12, compilation, package imports, the full test suite and CLI smoke paths including real rule-engine findings and quality-gate exit behavior.

## Repository layout

```text
src/sqlstudio/              Production Python package
  parser/                   SQL tokenizer and parser
  dependencies/             Canonical dependency graph and resolver
  cross_reference/          Incoming/outgoing cross references
  impact_analysis/          Change-impact traversal and reporting
  circular_dependencies/    SCC-based cycle detection
  dead_objects/             Conservative dead-object candidate analysis
  rules/                    Shared rule context, severities, findings and built-in rules
cli/sqlstudio.py            Repository-local CLI
tests/                      Automated tests
docs/                       Architecture, CLI and functional contracts
examples/                   Reproducible SQL examples
```

Legacy or experimental areas such as benchmark/profiler are not considered completed MVP capabilities until their behavior is implemented and tested.

## Documentation

- [Architecture](docs/architecture.md)
- [CLI](docs/CLI.md)
- [Static-analysis Rule Engine contract](docs/static-analysis-rule-engine.md)
- [Impact Report contract](docs/impact-report.md)
- [Circular Dependency Detection contract](docs/circular-dependency-detection.md)
- [Dead Object Detection contract](docs/dead-object-detection.md)
- [Roadmap](docs/roadmap.md)
- [Development audit — historical baseline](docs/development-audit.md)
- [Development audit — remediation status](docs/development-audit-remediation.md)
- [AI development rules](AI_DEVELOPMENT.md)

## Development rule

Git is the source of truth. Functional changes require tests, reproducible validation and Conventional Commits. See `AI_DEVELOPMENT.md` for the repository working agreement.
