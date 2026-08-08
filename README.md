# SQL Studio

SQL Studio is a Python 3.12+ toolkit for static analysis of SQL repositories.

**Current version:** `0.18.0`  
**Development status:** stabilized MVP static-analysis core with installable packaging and a representative T-SQL parser regression corpus. Next milestone is repository hygiene around legacy handoff directories.

## Implemented capabilities

- repository scanning and JSON repository model;
- T-SQL tokenization and parsing with representative complex-syntax regression coverage;
- SQL object, parameter, variable and reference extraction;
- bracketed/multipart identifier normalization, CTE/temp suppression and multi-reference extraction;
- directed dependency graph;
- dependency serialization;
- cross-reference analysis;
- transitive impact analysis;
- circular dependency detection using strongly connected components;
- conservative dead-object candidate detection;
- consolidated static-analysis Rule Engine with normalized severities/findings;
- CI quality gates through `analyze --fail-on`;
- JSON and self-contained HTML impact reports;
- installable Python package with wheel/sdist distributions;
- `sqlstudio` console command plus repository-wrapper compatibility;
- automated validation in GitHub Actions.

## Installation

From a repository checkout:

```bash
python -m pip install .
sqlstudio --version
```

For development:

```bash
python -m pip install -e .
```

Build distributable artifacts with:

```bash
python -m pip install build
python -m build
```

This produces a source distribution and a platform-independent wheel under `dist/`. SQL Studio is installable but is **not automatically published to PyPI**.

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

## Parser boundary

The parser is a dependency-oriented static parser, not a full T-SQL compiler. The `0.18.0` regression corpus covers bracketed/multipart names, multiple joins, CTEs, derived tables, `MERGE`, alias-targeted `UPDATE`, temp-table suppression and escaped string literals.

Dynamic SQL and runtime/external constructs remain uncertainty boundaries. SQL-project style sources with one primary schema object per file are the supported repository shape. See [T-SQL Parser Support Contract](docs/parser-support.md) for the precise scope and limitations.

## Rule Engine

Structural services such as Dependency, Cross Reference and Impact remain independent APIs. Actionable detections are consolidated through `StaticAnalysisRuleEngine`.

Built-in rules:

- `SQL001` — Circular dependency — `error`;
- `SQL002` — Dead object candidate — `warning`.

`StaticAnalysisAnalyzer` parses each SQL input once, builds one dependency graph and shares that context across all selected rules. Existing dedicated analyzers/commands remain supported.

## Dead-object safety contract

Dead Object Detection produces **candidates only**. It never asserts that an object is safe to delete.

A candidate can still be used by application code, SQL Agent jobs, ETL/orchestration, reporting tools, external databases, permissions-driven workflows or dynamic SQL that is not statically resolvable. Known externally invoked SQL objects can be supplied with repeatable `--entry-point` arguments. Triggers are excluded by default because their invocation is implicit.

## Performance tooling boundary

Runtime profiling and benchmark tooling are explicitly **post-MVP**. Earlier repository scripts only generated empty templates or stored caller-supplied metrics; they did not perform real measurement and have been removed from the supported baseline.

Any future profiler/benchmark implementation must cross a documented re-entry gate covering metric provenance, database/runtime boundaries, safety, reproducibility, versioned schemas, tests and CI. See [Performance Tooling Scope Decision](docs/performance-tooling-scope.md).

## Quick start

```bash
sqlstudio --help
sqlstudio parse examples/sample_procedure.sql
sqlstudio dependencies examples/sample_procedure.sql
sqlstudio cross-references examples/sample_procedure.sql
sqlstudio impact sys.objects examples/sample_procedure.sql
sqlstudio circular-dependencies examples/circular_dependencies
sqlstudio dead-objects examples/dead_objects --entry-point dbo.Entry
sqlstudio analyze examples/dead_objects --entry-point dbo.Entry
sqlstudio analyze examples/circular_dependencies --rule SQL001 --fail-on error
```

`analyze --fail-on` returns exit code `2` when the configured finding threshold is reached. Exit code `1` remains reserved for handled execution/input failures.

The historical repository invocation remains supported:

```bash
python cli/sqlstudio.py --help
```

That file is a compatibility wrapper over the canonical `sqlstudio.cli` implementation.

## Validation

```bash
PYTHONPATH=src python -m unittest discover -s tests -p "test_*.py" -v
python -m build
```

GitHub Actions validates Python 3.12, compilation, package imports, the full test suite, the representative parser fixture, legacy wrapper smoke paths, wheel/sdist construction and the installed `sqlstudio` command from outside the repository checkout.

## Repository layout

```text
pyproject.toml               Standard Python build/install metadata
src/sqlstudio/               Production Python package
  cli.py                     Canonical command-line implementation
  parser/                    SQL tokenizer, parser and name normalization
  dependencies/              Canonical dependency graph and resolver
  cross_reference/           Incoming/outgoing cross references
  impact_analysis/           Change-impact traversal and reporting
  circular_dependencies/     SCC-based cycle detection
  dead_objects/              Conservative dead-object candidate analysis
  rules/                     Shared rule context, severities, findings and built-in rules
cli/sqlstudio.py             Repository-checkout compatibility wrapper
tests/fixtures/tsql_complex/ Representative dependency-oriented T-SQL corpus
tests/                       Automated tests
docs/                        Architecture, CLI, packaging and functional contracts
examples/                    Reproducible SQL examples
```

Performance profiler/benchmark concepts are deliberately outside the current production tree until the documented post-MVP re-entry gate is satisfied.

## Documentation

- [Architecture](docs/architecture.md)
- [CLI](docs/CLI.md)
- [Packaging and installation](docs/packaging.md)
- [T-SQL Parser Support Contract](docs/parser-support.md)
- [Performance Tooling Scope Decision](docs/performance-tooling-scope.md)
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
