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
  -> JSON / HTML / CLI
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

Changing this direction would break Cross Reference, Impact Analysis, Circular Dependency Detection and Dead Object Detection semantics.

## 5. Cross Reference Engine

Cross Reference exposes direct incoming/outgoing relationships and deterministic JSON serialization.

## 6. Impact Analysis Engine

Impact Analysis answers which SQL objects can be affected if a selected object changes. Because graph edges point from dependent to dependency, it traverses `dependents_of()` transitively. Direct and indirect HTML impact is derived from the in-memory impact tree. Impact JSON schema `1.0` remains deliberately flat.

## 7. Circular Dependency Engine

Circular Dependency Detection computes strongly connected components with Tarjan's algorithm. A finding is returned for a component of two or more mutually reachable objects or a one-object self-reference. One SCC is the stable reporting unit; SQL Studio does not enumerate every possible cyclic path.

## 8. Dead Object Engine

Dead Object Detection answers a narrower and deliberately conservative question:

> Which locally defined SQL object components have no incoming static references from outside the component?

The result is a **candidate review list**, not deletion proof.

### Supported definitions

Only schema objects recognized as `Stored Procedure`, `View`, `Function`, `Table` or `Trigger` participate. `Unknown` reference-only nodes and synthetic `Script` objects are not candidates.

### Component semantics

Circular components are reused from the SCC engine. If `A` and `B` only reference each other and nothing outside the component references either object, they are returned as one candidate finding rather than disappearing because each has an internal incoming edge.

### Entry-point exclusions

- callers may declare known external entry points explicitly;
- a root component containing a declared entry point is excluded;
- `Trigger` is an implicit entry-object type and root components containing a trigger are excluded automatically.

Entry-point names are matched case-insensitively and must resolve to a locally defined supported object.

### Uncertainty contract

Every finding exposes `external_usage_possible=true`. The analyzer counts parsed objects containing dynamic SQL and the serializer emits `dynamic_sql_may_hide_dependencies` when that count is non-zero. External application calls, jobs, ETL, reports and other systems are outside repository-only static evidence.

JSON schema `1.0` therefore declares `classification="candidate_only"` and `safe_to_delete=false`.

## 9. CLI boundary

`cli/sqlstudio.py` resolves SQL inputs, invokes package analyzers, writes output and maps handled validation/filesystem errors to exit code `1`. Business semantics stay in `src/sqlstudio`.

## 10. Validation boundary

The baseline targets Python 3.12+. GitHub Actions compiles sources, validates imports, runs the full unit-test suite and exercises CLI smoke paths against reproducible fixtures, including a real cycle and a dead-object candidate with an explicit entry point.

## 11. Deferred architecture

Static-analysis rule consolidation, packaging/installation, automated profiling and benchmarking remain separate roadmap items.
