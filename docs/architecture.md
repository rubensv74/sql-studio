# SQL Studio Architecture

## 1. Architectural goal

SQL Studio performs static analysis over SQL source files without requiring a live database connection. Production implementation lives under `src/sqlstudio/`; the CLI orchestrates package APIs but does not redefine their semantics.

## 2. Main flow

```text
SqlSource[]
  -> SQLParser
  -> SqlDocument / SqlObject / Reference
  -> DependencyResolver
  -> DependencyGraph
       -> CrossReference Engine
       -> Impact Analysis Engine
       -> Circular Dependency Engine
       -> Dead Object Engine
       -> StaticAnalysisRuleEngine
            -> SQL001 Circular Dependency
            -> SQL002 Dead Object Candidate
       -> RepositoryAnalysisEngine
            -> RepositoryAnalysisResult
                 -> JSON schema 1.0
                 -> self-contained HTML
  -> CLI
```

`RepositoryAnalysisEngine` is a product-level composition layer, not a second parser or dependency engine. It parses each physical source once, resolves one canonical graph and reuses that graph/context for repository inventory, rule findings, circular components, dead-object candidates and report views.

Distribution flow is separate from business semantics:

```text
src/sqlstudio
  -> pyproject.toml / setuptools
  -> sdist + wheel
  -> installed console entry point: sqlstudio
  -> sqlstudio.cli:main
```

## 3. Physical source and parser boundary

`SqlSource` is the physical repository-input model. Its `source_id` remains independent from SQL schema-object identity. Durable definitions keep their SQL names; script-only scopes use `script:<source_id>`.

The parser is dependency-oriented rather than a complete T-SQL compiler. It extracts supported schema objects, references and execution metadata from repository source files.

### Object-scoped ownership

A `SqlDocument` may contain multiple durable `SqlObject` definitions from the same source file. `ParserContext` keeps one active object scope and materializes it when a new durable definition starts, a standalone `GO` batch separator is reached, or the document ends.

Each scope owns its own:

- parameters;
- variables;
- references and calls;
- temporary tables;
- dynamic-SQL evidence.

Those collections are reset between scopes. This prevents evidence from one stored procedure, view or table from leaking into another object defined in the same physical `.sql` file.

Standalone `GO` is recognized only when it occupies its own source line. Guarded migration DDL such as `IF OBJECT_ID(...) ... CREATE TABLE ...` is supported when ownership can be established. Permanent runtime DDL inside an already active stored module is not promoted to a separate top-level durable repository definition.

The public AST remains unchanged: `SqlDocument.objects` was already a collection and `SqlObject` already carried the required object-level evidence. `DependencyResolver` therefore continues consuming the same public models without a second graph implementation.

The tokenizer preserves supported multipart identifiers as one logical token, including bracket-quoted segments such as `[OtherDb].[sales].[Order Header]`. Shared name normalization removes bracket syntax when materializing `SqlObject` and `Reference` fields.

Reference extraction scans all resolvable relation clauses in a statement rather than stopping at the first `FROM`/`JOIN`. Representative support includes CTE bodies, derived tables, `MERGE ... USING`, alias-targeted `UPDATE`, `APPLY`, three-part names and transient temp/table-variable suppression. CTE aliases and transient objects are not durable dependency targets.

`DependencyResolver` resolves documents in two passes:

1. register every locally defined object and its real `object_type`;
2. resolve references and dependency edges.

This guarantees that a local definition does not remain `Unknown` merely because another input file referenced it first. Reference-only external nodes remain `Unknown`.

Dynamic execution through `EXEC(...)` or `sp_executesql` is flagged on the owning parsed SQL object so higher-level analyses can surface uncertainty. Dynamic SQL is not recursively promoted to guaranteed dependency evidence.

The parser support contract is versioned in `docs/parser-support.md`; object ownership is frozen in `docs/object-scoped-parser.md`; physical identity is frozen in `docs/sql-source-identity.md`.

## 4. Dependency Engine

The canonical edge direction is:

```text
source -> target
```

where `source` depends on `target`.

`DependencyGraph` exposes:

- `dependencies_of(name)`: outgoing targets used by `name`;
- `dependents_of(name)`: incoming sources that depend on `name`.

Changing this direction would break Cross Reference, Impact Analysis, Circular Dependency Detection, Dead Object Detection, Rule Engine and Repository Analysis semantics.

## 5. Cross Reference Engine

Cross Reference exposes direct incoming/outgoing relationships and deterministic JSON serialization.

## 6. Impact Analysis Engine

Impact Analysis answers which SQL objects can be affected if a selected object changes. Because graph edges point from dependent to dependency, it traverses `dependents_of()` transitively. Direct and indirect HTML impact is derived from the in-memory impact tree. Impact JSON schema `1.0` remains deliberately flat.

Impact stays an on-demand specialized capability. Repository Analysis does not precompute a transitive impact tree for every object.

## 7. Circular Dependency Engine

Circular Dependency Detection computes strongly connected components with Tarjan's algorithm. A finding is returned for a component of two or more mutually reachable objects or a one-object self-reference. One SCC is the stable reporting unit; SQL Studio does not enumerate every possible cyclic path.

## 8. Dead Object Engine

Dead Object Detection asks which locally defined SQL object components have no incoming static references from outside the component. The result is a **candidate review list**, not deletion proof.

Only schema objects recognized as `Stored Procedure`, `View`, `Function`, `Table` or `Trigger` participate. `Unknown` reference-only nodes and synthetic `Script` objects are not candidates.

Circular components reuse the SCC engine. Explicit external entry points suppress candidate roots, and root components containing a trigger are excluded automatically because trigger invocation is implicit.

Every finding preserves external-usage uncertainty. Dead Object JSON schema `1.0` declares `classification="candidate_only"` and `safe_to_delete=false`.

## 9. Static-analysis Rule Engine

The Rule Engine consolidates **actionable findings**, not every SQL Studio service.

Dependency, Cross Reference and Impact remain structural analysis services. Circular Dependency and Dead Object engines remain valid dedicated APIs and are adapted into built-in rules.

`StaticAnalysisAnalyzer` parses all source inputs once and resolves one `DependencyGraph`. It creates a shared `RuleContext`; rules must not reparse inputs or create alternate graph semantics.

Every `StaticAnalysisRule` exposes a stable ID, title, description, default severity and `evaluate(context)` operation. The normalized output layers are:

```text
StaticAnalysisRule
  -> RuleResult
       -> Finding
            -> Severity (info | warning | error)
  -> StaticAnalysisResult
```

Built-in IDs are `SQL001` Circular Dependency (`error`) and `SQL002` Dead Object Candidate (`warning`).

The Rule Engine is additive. Dedicated `circular-dependencies` and `dead-objects` contracts remain supported. The consolidated `analyze` command is preferred when one normalized rule report or severity gate is required.

## 10. Unified Repository Analysis

`RepositoryAnalysisEngine` composes the stable parser, resolver and graph algorithms into one product-level repository result.

The execution contract is:

1. canonicalize and deduplicate `SqlSource` inputs by source identity;
2. parse each source exactly once;
3. resolve one `DependencyGraph`;
4. create one shared `RuleContext`;
5. run the static-analysis rules over that context;
6. run circular and dead-object engines over the same graph;
7. pair each original `SqlSource` with its parsed document to create source/object provenance;
8. enrich local object records with direct dependencies and dependents from the canonical graph;
9. return one immutable `RepositoryAnalysisResult`.

`RepositoryAnalysisResult` is then consumed independently by:

- `RepositoryAnalysisSerializer` — new JSON schema `1.0`;
- `RepositoryAnalysisReportGenerator` — self-contained HTML.

The HTML generator never reparses SQL and never defines alternate analysis semantics. Existing specialized JSON schemas are not embedded by mutation; the unified serializer owns its own explicit schema namespace.

The unified report deliberately excludes volatile execution metadata such as timestamps, machine names and inferred Git state from schema `1.0`, keeping repeated analysis deterministic for the same source contents/configuration.

Key-object ranking is based on direct incoming dependents. It is an informational centrality signal, not a new static-analysis rule or severity.

The complete contract is frozen in `docs/unified-repository-analysis.md`.

## 11. Packaging and CLI boundary

`src/sqlstudio/cli.py` is the canonical CLI implementation. Package metadata declares the installed console entry point `sqlstudio = sqlstudio.cli:main`.

`cli/sqlstudio.py` is a compatibility wrapper for direct repository execution. It must not contain a second implementation of CLI business behavior.

The canonical package version lives in `src/sqlstudio/_version.py`, is exported as `sqlstudio.__version__`, and is consumed dynamically by `pyproject.toml`. `core/version.txt` remains a compatibility mirror guarded by tests.

The package uses a `src/` layout and setuptools PEP 517 backend to build sdist and platform-independent wheel artifacts. Packaging does not alter analysis semantics.

CLI exit codes remain:

- `0`: normal success;
- `1`: handled execution/input failure;
- `2`: successful `analyze` execution whose findings meet the requested `--fail-on` threshold.

`repository-analysis` uses the normal success/error codes and does not introduce a new quality-gate exit code in schema/CLI version `1.0`.

## 12. Validation boundary

The baseline targets Python 3.12+. GitHub Actions compiles sources, validates imports, runs the full unit-test suite, exercises representative complex-T-SQL and object-scope corpora plus the repository wrapper, builds sdist/wheel, installs the wheel and executes `sqlstudio` from outside the checkout with `PYTHONPATH` cleared.

Repository Analysis is considered distributable only when both JSON schema `1.0` and self-contained HTML can be generated through the installed wheel outside the checkout.

A source-only green test suite is insufficient to validate packaging or parser/report distribution behavior.

## 13. Performance tooling boundary

Runtime profiling and performance benchmarking are **not part of the current MVP architecture**.

The removed legacy artifacts did not measure workloads: the profiler created an empty template and the benchmark script persisted values supplied by the caller. They also lacked package integration, tests and one coherent schema contract.

A future profiler would introduce a live/runtime database boundary with credentials, permissions, telemetry sensitivity, observer overhead and server-version concerns. A future benchmark facility would require a reproducible corpus, repeat/variance semantics, environment metadata and stable baseline comparison.

Performance tooling may only re-enter after satisfying the contract in `docs/performance-tooling-scope.md`. Future implementation must live under `src/sqlstudio/` and must not silently change the repository-only static-analysis boundary of existing analyzers.

## 14. Release boundary

The current release channel is GitHub Releases only and remains separate from analysis semantics. PyPI publication and runtime profiler/benchmark tooling require separate explicit decisions.
