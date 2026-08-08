# SQL Studio

SQL Studio is a Python 3.12+ toolkit for static analysis of SQL repositories.

**Current version:** `0.21.0`  
**Development status:** stabilized MVP static-analysis core with installable packaging, controlled GitHub Releases, evidence-driven parser hardening and object-scoped multi-definition parsing. PyPI publication remains explicitly deferred.

## Implemented capabilities

- repository scanning and JSON repository model;
- T-SQL tokenization and parsing with representative complex-syntax regression coverage;
- multiple durable SQL objects per `.sql` source with isolated object-scoped evidence;
- SQL object, parameter, variable and reference extraction;
- bracketed/multipart identifier normalization, CTE/temp suppression and multi-reference extraction;
- standalone `GO` batch-boundary handling;
- guarded migration DDL discovery;
- stored-procedure parameters with or without parentheses;
- transient `CREATE TABLE #temp` handling without durable graph pollution;
- built-in rowset suppression for `OPENJSON`, `OPENQUERY` and `OPENROWSET`;
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
- canonical `handoffs/` repository path for handoff notes;
- controlled GitHub Release automation after successful `main` CI;
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

This produces a source distribution and a platform-independent wheel under `dist/`. SQL Studio is installable and GitHub Releases attach both artifacts. It is **not published to PyPI** under the current policy.

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

The parser is dependency-oriented, not a full T-SQL compiler. The representative regression corpus covers bracketed/multipart names, multiple joins, CTEs, derived tables, `MERGE`, alias-targeted `UPDATE`, temporary-object suppression, JSON rowsets, guarded migration DDL, multi-definition source files and escaped string literals.

### Object-scoped ownership

One physical `.sql` file may define several durable schema objects. SQL Studio emits each as its own `SqlObject` and isolates:

- parameters;
- variables;
- references/calls;
- temporary tables;
- dynamic-SQL evidence.

The active scope closes when a new durable definition starts, a standalone `GO` batch boundary is reached, or the document ends. This prevents dependency evidence from one object leaking into another object defined later in the same file.

Dynamic SQL and runtime/external constructs remain uncertainty boundaries. Multi-definition support is guaranteed only when source structure provides reliable ownership boundaries; SQL Studio prefers incomplete evidence over a misleading graph.

See [T-SQL Parser Support Contract](docs/parser-support.md), [Object-Scoped Parser Architecture](docs/object-scoped-parser.md) and [Real Repository Validation — Pass 1](docs/real-repository-validation.md).

## Rule Engine

Structural services such as Dependency, Cross Reference and Impact remain independent APIs. Actionable detections are consolidated through `StaticAnalysisRuleEngine`.

Built-in rules:

- `SQL001` — Circular dependency — `error`;
- `SQL002` — Dead object candidate — `warning`.

`StaticAnalysisAnalyzer` parses each SQL input once, builds one dependency graph and shares that context across all selected rules. Existing dedicated analyzers/commands remain supported.

## Dead-object safety contract

Dead Object Detection produces **candidates only**. It never asserts that an object is safe to delete.

A candidate can still be used by application code, SQL Agent jobs, ETL/orchestration, reporting tools, external databases, permissions-driven workflows or dynamic SQL that is not statically resolvable. Known externally invoked SQL objects can be supplied with repeatable `--entry-point` arguments. Triggers are excluded by default because their invocation is implicit.

## Repository handoffs

`handoffs/` is the canonical path for repository handoff notes. The legacy singular `handoff/` path has been removed; `sqlstudio new-handoff <name>` continues to create `handoffs/<name>.md`.

See [Handoff Repository Layout](docs/handoff-layout.md) for the compatibility decision.

## Release policy

SQL Studio uses controlled **GitHub Releases only**. A successful `CI` run for `main` triggers the release workflow, which resolves the package version, enforces immutable `vMAJOR.MINOR.PATCH` tags, builds the wheel/sdist and creates the GitHub Release when that version has not yet been released.

PyPI publication is explicitly excluded from this workflow. See [Release Policy](docs/release-policy.md) and [Main Branch Protection](docs/branch-protection.md).

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

GitHub Actions validates Python 3.12, compilation, package imports, the full test suite, representative complex/parser ownership fixtures, legacy wrapper smoke paths, wheel/sdist construction and the installed `sqlstudio` command from outside the repository checkout.

## Repository layout

```text
pyproject.toml                         Standard Python build/install metadata
src/sqlstudio/                         Production Python package
  cli.py                               Canonical command-line implementation
  parser/                              SQL tokenizer, parser and object-scope ownership
  dependencies/                        Canonical dependency graph and resolver
  cross_reference/                     Incoming/outgoing cross references
  impact_analysis/                     Change-impact traversal and reporting
  circular_dependencies/               SCC-based cycle detection
  dead_objects/                        Conservative dead-object candidate analysis
  rules/                               Shared rule context, severities, findings and built-in rules
cli/sqlstudio.py                       Repository-checkout compatibility wrapper
handoffs/                              Canonical handoff notes/template
tests/fixtures/tsql_complex/           Representative dependency-oriented T-SQL corpus
tests/fixtures/real_repository/        Reduced cases derived from real-repository failures
tests/fixtures/object_scopes/          Multi-definition ownership and batch-boundary corpus
tests/                                 Automated tests
docs/                                  Architecture, CLI, packaging and functional contracts
examples/                              Reproducible SQL examples
```

Performance profiler/benchmark concepts are deliberately outside the current production tree until the documented post-MVP re-entry gate is satisfied.

## Documentation

- [Architecture](docs/architecture.md)
- [CLI](docs/CLI.md)
- [Packaging and installation](docs/packaging.md)
- [T-SQL Parser Support Contract](docs/parser-support.md)
- [Object-Scoped Parser Architecture](docs/object-scoped-parser.md)
- [Real Repository Validation — Pass 1](docs/real-repository-validation.md)
- [Handoff Repository Layout](docs/handoff-layout.md)
- [Release Policy](docs/release-policy.md)
- [Main Branch Protection](docs/branch-protection.md)
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
