# SQL Studio Architecture

## 1. Architectural goal

SQL Studio performs static analysis over SQL source files without requiring a live database connection. Production implementation lives under `src/sqlstudio/`; the CLI orchestrates package APIs but does not redefine their semantics.

## 2. Main flow

```text
SQL files
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
  -> JSON / HTML / CLI
```

Distribution flow is separate from business semantics:

```text
src/sqlstudio
  -> pyproject.toml / setuptools
  -> sdist + wheel
  -> installed console entry point: sqlstudio
  -> sqlstudio.cli:main
```

## 3. Parser and definition metadata

The parser extracts supported schema objects, references and execution metadata. `DependencyResolver` resolves documents in two passes:

1. register every locally defined object and its real `object_type`;
2. resolve references and dependency edges.

This guarantees that a local definition does not remain `Unknown` merely because another input file referenced it first. Reference-only external nodes remain `Unknown`.

Dynamic execution through `EXEC(...)` or `sp_executesql` is flagged on the parsed SQL object so higher-level analyses can surface uncertainty.

## 4. Dependency Engine

The canonical edge direction is:

```text
source -> target
```

where `source` depends on `target`.

`DependencyGraph` exposes:

- `dependencies_of(name)`: outgoing targets used by `name`;
- `dependents_of(name)`: incoming sources that depend on `name`.

Changing this direction would break Cross Reference, Impact Analysis, Circular Dependency Detection, Dead Object Detection and Rule Engine semantics.

## 5. Cross Reference Engine

Cross Reference exposes direct incoming/outgoing relationships and deterministic JSON serialization.

## 6. Impact Analysis Engine

Impact Analysis answers which SQL objects can be affected if a selected object changes. Because graph edges point from dependent to dependency, it traverses `dependents_of()` transitively. Direct and indirect HTML impact is derived from the in-memory impact tree. Impact JSON schema `1.0` remains deliberately flat.

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

The Rule Engine is additive. Dedicated `circular-dependencies` and `dead-objects` contracts remain supported. The consolidated `analyze` command is preferred when one normalized report or severity gate is required.

## 10. Packaging and CLI boundary

`src/sqlstudio/cli.py` is the canonical CLI implementation. Package metadata declares the installed console entry point `sqlstudio = sqlstudio.cli:main`.

`cli/sqlstudio.py` is a compatibility wrapper for direct repository execution. It must not contain a second implementation of CLI business behavior.

The canonical package version lives in `src/sqlstudio/_version.py`, is exported as `sqlstudio.__version__`, and is consumed dynamically by `pyproject.toml`. `core/version.txt` remains a compatibility mirror guarded by tests.

The package uses a `src/` layout and setuptools PEP 517 backend to build sdist and platform-independent wheel artifacts. Packaging does not alter analysis semantics.

CLI exit codes remain:

- `0`: normal success;
- `1`: handled execution/input failure;
- `2`: successful `analyze` execution whose findings meet the requested `--fail-on` threshold.

## 11. Validation boundary

The baseline targets Python 3.12+. GitHub Actions compiles sources, validates imports, runs the full unit-test suite, exercises the repository wrapper, builds sdist/wheel, installs the wheel and executes `sqlstudio` from outside the checkout with `PYTHONPATH` cleared.

A source-only green test suite is insufficient to validate packaging.

## 12. Deferred architecture

Profiler/benchmark scope and publication/release automation remain separate roadmap decisions.
