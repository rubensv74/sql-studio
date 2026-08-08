# SQL Studio

SQL Studio is a Python 3.12+ toolkit for static analysis of SQL repositories.

**Current version:** `0.24.0`  
**Development status:** stabilized MVP static-analysis core with installable packaging, controlled GitHub Releases, evidence-driven parser hardening, object-scoped multi-definition parsing and physical SQL source identity. PyPI publication remains explicitly deferred.

## Implemented capabilities

- repository scanning and JSON repository model;
- `SqlSource` physical-source identity for repository/file analysis;
- T-SQL tokenization and dependency-oriented parsing;
- multiple durable SQL objects per `.sql` source with isolated object-scoped evidence;
- SQL object, parameter, variable and reference extraction;
- SQL Server procedure/function parameters with parameterized datatypes, defaults and `OUTPUT` markers;
- inline `FOREIGN KEY ... REFERENCES` dependency extraction;
- bracketed/multipart identifier normalization, CTE/temp suppression and multi-reference extraction;
- standalone `GO` batch-boundary handling;
- guarded migration DDL discovery;
- transient `CREATE TABLE #temp` handling without durable graph pollution;
- built-in rowset suppression for `OPENJSON`, `OPENQUERY` and `OPENROWSET`;
- directed dependency graph, cross references and transitive impact analysis;
- circular dependency detection using strongly connected components;
- conservative dead-object candidate detection;
- consolidated static-analysis Rule Engine with severity gates;
- JSON and self-contained HTML impact reports;
- installable Python package with wheel/sdist distributions;
- `sqlstudio` console command plus repository-wrapper compatibility;
- controlled GitHub Release automation after successful `main` CI.

## Installation

```bash
python -m pip install .
sqlstudio --version
```

For development:

```bash
python -m pip install -e .
python -m build
```

SQL Studio is installable and GitHub Releases attach wheel and sdist artifacts. It is **not published to PyPI** under the current policy.

## Dependency semantics

The graph stores:

```text
source -> target
```

meaning `source` depends on `target`.

Therefore:

- `dependencies_of(A)` answers what A uses;
- `dependents_of(A)` answers what uses A;
- Impact Analysis walks `dependents_of()` transitively;
- Circular Dependency Detection reports strongly connected components;
- Dead Object Detection reviews durable components with no incoming static references from outside the component.

## Physical SQL source identity

Repository SQL is not always a schema definition. Seed, migration and maintenance files can contain real dependencies while defining no procedure, view, function or table.

`0.24.0` introduces:

```python
from sqlstudio import SqlSource

source = SqlSource(
    source_id="sql/import/003_seed_import_columns_v3.sql",
    sql_text="SELECT * FROM warroom.ImportColumnDefinition;",
)
```

Source-aware parsing maps only fallback script scopes to:

```text
script:sql/import/003_seed_import_columns_v3.sql
```

A durable object such as `dbo.Report` keeps its SQL identity even when parsed through `SqlSource`.

All repository-facing analyzers expose `analyze_source()` / `analyze_sources()`. Existing raw-text `parse()`, `analyze()` and `analyze_many()` methods remain compatible. The CLI uses the source-aware path so independent physical scripts no longer collapse into one `UnnamedScript` graph node.

See [SQL Source Identity](docs/sql-source-identity.md).

## Parser boundary

The parser is dependency-oriented, not a full T-SQL compiler. The regression corpus covers multipart/bracketed names, multiple joins, CTEs, derived tables, `MERGE`, alias-targeted `UPDATE`, temporary-object suppression, JSON rowsets, guarded migration DDL, multi-definition files, inline foreign keys, real procedure signatures and escaped string literals.

One physical source may define several durable objects. Each object owns only its own parameters, variables, references/calls, temporary tables and dynamic-SQL evidence. Dynamic SQL and runtime/external constructs remain uncertainty boundaries.

Stored procedure/function parameter parsing distinguishes optional outer signature parentheses from datatype parentheses such as `nvarchar(320)`, `decimal(18,4)` and `datetime2(3)`. `SET @Parameter = ...` does not reclassify an existing parameter as a local variable.

Inline foreign keys are represented with the same graph direction: `Child -> Parent`. Standalone `ALTER TABLE ... FOREIGN KEY` ownership remains deferred until representative repository evidence requires it.

See [T-SQL Parser Support Contract](docs/parser-support.md) and [Object-Scoped Parser Architecture](docs/object-scoped-parser.md).

## Rule Engine and dead-object safety

Built-in rules:

- `SQL001` — Circular dependency — `error`;
- `SQL002` — Dead object candidate — `warning`.

Dead Object Detection produces **candidates only** and never asserts an object is safe to delete. Script nodes are not dead-object candidates. Known externally invoked objects can be supplied with repeatable `--entry-point` arguments.

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

Historical repository invocation remains supported:

```bash
python cli/sqlstudio.py --help
```

## Validation

```bash
PYTHONPATH=src python -m unittest discover -s tests -p "test_*.py" -v
python -m build
```

GitHub Actions validates Python 3.12, compilation, imports, the full test suite, source-aware script identity, representative parser fixtures, legacy wrapper smoke paths, wheel/sdist construction and execution of the installed `sqlstudio` command outside the repository checkout.

## Release policy

SQL Studio uses controlled **GitHub Releases only**. Successful `main` CI triggers the release workflow, which validates version identity, builds wheel/sdist artifacts and creates the SemVer release when it does not already exist. PyPI publication is explicitly excluded.

See [Release Policy](docs/release-policy.md) and [Main Branch Protection](docs/branch-protection.md).

## Documentation

- [Architecture](docs/architecture.md)
- [CLI](docs/CLI.md)
- [Packaging and installation](docs/packaging.md)
- [SQL Source Identity](docs/sql-source-identity.md)
- [T-SQL Parser Support Contract](docs/parser-support.md)
- [Object-Scoped Parser Architecture](docs/object-scoped-parser.md)
- [Real Repository Validation — Pass 1](docs/real-repository-validation.md)
- [Real Repository Validation — Pass 2](docs/real-repository-validation-pass-2.md)
- [Real Repository Validation — Pass 3](docs/real-repository-validation-pass-3.md)
- [Handoff Repository Layout](docs/handoff-layout.md)
- [Performance Tooling Scope Decision](docs/performance-tooling-scope.md)
- [Static-analysis Rule Engine contract](docs/static-analysis-rule-engine.md)
- [Impact Report contract](docs/impact-report.md)
- [Circular Dependency Detection contract](docs/circular-dependency-detection.md)
- [Dead Object Detection contract](docs/dead-object-detection.md)
- [Roadmap](docs/roadmap.md)

## Development rule

Git is the source of truth. Functional changes require tests, reproducible validation and Conventional Commits. See `AI_DEVELOPMENT.md`.
