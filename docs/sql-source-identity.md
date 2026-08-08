# SQL Source Identity

## Status

Frozen architecture contract for SQL Studio `0.24.0`.

## Problem

Not every repository SQL file defines a durable schema object. Seed, migration,
maintenance and deployment scripts can still reference durable SQL objects.
Before `0.24.0`, text-only parsing represented such files as `UnnamedScript`.
When multiple physical files were analyzed together, the dependency graph could
merge them into one node because graph identity is name-based.

That behavior destroyed physical-source provenance and could attribute a
reference from one script to another script.

## Decision

SQL Studio introduces `SqlSource` as an input-layer model:

```text
SqlSource
  source_id   stable caller-controlled physical identity
  sql_text    SQL content
  path        optional physical path metadata
```

`SqlSource` is deliberately outside the public SQL AST. `SqlDocument`,
`SqlObject` and `Reference` remain unchanged.

The canonical source-aware parser entry point is:

```python
SQLParser().parse_source(SqlSource(...))
```

The existing text-only entry point remains supported:

```python
SQLParser().parse(sql_text)
```

## Script node identity

A source-aware parse changes identity only for fallback script scopes whose
historical object is:

```text
object_type = Script
name        = UnnamedScript
```

Those scopes become:

```text
script:<source_id>
```

Example:

```text
sql/import/003_seed_import_columns_v3.sql
```

becomes:

```text
script:sql/import/003_seed_import_columns_v3.sql
```

Durable SQL definitions keep their SQL identity. A view `dbo.Report` located in
`sql/views/report.sql` remains `dbo.Report`; it does not become a source-path
node.

## Source ID normalization

`source_id` is caller-controlled and must be non-empty. SQL Studio normalizes
backslashes to `/` and removes leading `./` segments.

The CLI derives source IDs from file paths relative to the current working
directory when possible. This makes repository-root execution produce stable
repository-relative identities. Files outside the working directory retain an
absolute POSIX-style path.

Integrations that require stronger stability should construct `SqlSource`
directly and provide their own repository-relative `source_id`.

## Analysis APIs

Text-only compatibility methods remain available, including `analyze()` and
`analyze_many()`.

Source-aware methods are the canonical path for repository analysis:

- `DependencyAnalyzer.analyze_source()` / `analyze_sources()`
- `CrossReferenceAnalyzer.analyze_source()` / `analyze_sources()`
- `ImpactAnalyzer.analyze_source()` / `analyze_sources()`
- `CircularDependencyAnalyzer.analyze_source()` / `analyze_sources()`
- `DeadObjectAnalyzer.analyze_source()` / `analyze_sources()`
- `StaticAnalysisAnalyzer.analyze_source()` / `analyze_sources()`

The CLI uses source-aware methods for file and directory analysis.

## Graph semantics

The canonical graph direction does not change:

```text
source -> target
```

For a script file that reads `warroom.ImportColumnDefinition` the graph may now
contain:

```text
script:sql/import/003_seed_import_columns_v3.sql
    -> warroom.ImportColumnDefinition
```

Two physical scripts must never collapse merely because neither defines a
schema object.

## Downstream safety

Script nodes remain object type `Script`. Dead Object Detection continues to
consider only supported durable schema-object types, so physical script nodes
do not become deletion candidates.

No Impact, Circular Dependency, Cross Reference or Rule Engine graph direction
is changed by this decision.

## Compatibility

`0.24.0` intentionally does not add `source_path` or `source_id` fields to the
public AST or existing serialized schemas.

Raw-text callers retain historical behavior, including `UnnamedScript` for
text-only fallback scopes. This is deliberate compatibility. Repository/file
analysis should use `SqlSource` to obtain physical identity.

The repository compatibility wrapper keeps its historical text-reader helper
while exposing the source-aware path internally.

## Gate

Future repository-level analysis must preserve physical source identity until
object ownership has been established. New code must not reduce file inputs to
bare SQL strings before dependency analysis when source provenance matters.
