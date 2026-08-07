# SQL Studio Architecture

## 1. Architectural goal

SQL Studio performs static analysis over SQL source files without requiring a
live database connection. The production implementation lives under
`src/sqlstudio/`; CLI code orchestrates those APIs but does not redefine their
semantics.

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
  -> JSON / HTML / CLI
```

## 3. Repository and parser layer

### Repository Engine

`RepositoryEngine` and the scanner model the repository and identify SQL source
files.

### SQL Parser

`src/sqlstudio/parser/` contains the tokenizer, token stream, parsing context,
AST structures and statement parsers. The parser extracts SQL objects and the
references needed by higher-level analyzers.

## 4. Dependency Engine

`DependencyResolver` converts parsed references into a directed graph.

The canonical edge direction is:

```text
source -> target
```

where `source` depends on `target`.

`DependencyGraph` therefore exposes two intentionally different navigations:

- `dependencies_of(name)`: outgoing targets used by `name`;
- `dependents_of(name)`: incoming sources that depend on `name`.

Changing this direction would break Cross Reference, Impact Analysis and
Circular Dependency Detection semantics and requires an explicit architecture
decision.

## 5. Cross Reference Engine

The Cross Reference Engine exposes direct relationship inspection over the
dependency graph.

Main components:

- `CrossReference`
- `CrossReferenceEngine`
- `CrossReferenceAnalyzer`
- `CrossReferenceSerializer`

Primary operations include incoming and outgoing references plus JSON
serialization.

## 6. Impact Analysis Engine

Impact Analysis answers:

> Which SQL objects can be affected if the selected object changes?

Because graph edges point from dependent to dependency, the engine starts at the
root object and traverses `dependents_of()` transitively.

The result contains:

- `root_object`;
- a deterministic flat `impacted_objects` collection;
- an in-memory hierarchical `ImpactNode` tree.

Cycles are handled by ancestry tracking so the traversal terminates without
duplicating objects indefinitely.

### Direct and indirect impact

- direct impacts are the first-level children of the root in the impact tree;
- indirect impacts are descendants at depth two or greater.

The HTML report derives its classification from that tree.

### JSON compatibility

`ImpactResultSerializer` schema `1.0` remains intentionally flat and does not
serialize the tree. A future JSON tree contract must use a new schema version.

## 7. Circular Dependency Engine

Circular Dependency Detection answers:

> Which groups of SQL objects form closed dependency loops?

`CircularDependencyEngine` operates directly on the canonical
`DependencyGraph`. It computes strongly connected components using Tarjan's
algorithm.

A finding is returned when:

- a strongly connected component contains two or more objects; or
- a single-object component contains a self-referencing edge.

A finding contains the deterministically sorted member names and every internal
dependency edge between those members. SQL object identity is compared
case-insensitively while the graph's canonical casing is preserved in output.

### Why SCCs instead of enumerated paths

One strongly connected component can contain many possible cyclic paths.
Enumerating every path can grow exponentially and produces duplicate
representations of the same architectural problem. SQL Studio therefore uses
one SCC as the stable unit of circular-dependency reporting.

Main components:

- `CircularDependency`
- `CircularDependencyEngine`
- `CircularDependencyAnalyzer`
- `CircularDependencySerializer`

JSON schema `1.0` includes a summary plus the members, self-reference flag and
internal edges of each circular component.

## 8. CLI boundary

`cli/sqlstudio.py` is a repository-local adapter. It is responsible for:

- resolving input SQL files;
- invoking package analyzers;
- formatting/writing output;
- returning stable exit codes.

Business semantics belong in `src/sqlstudio`, not in CLI conditionals.

## 9. Validation boundary

The baseline targets Python 3.12+. GitHub Actions compiles the code, validates
imports, runs the complete unit-test suite and exercises CLI smoke paths,
including `circular-dependencies`.

## 10. Deferred architecture

Packaging/installation, automated profiling, benchmarking and higher-level rule
engines remain outside the stabilized MVP baseline until explicitly promoted by
the roadmap.
