# SQL Source Identity

## Status

Frozen architecture contract introduced in SQL Studio `0.24.0` and clarified by real-repository dogfooding in `0.26.0`.

## Problem

Not every repository SQL file defines a durable schema object. Seed, migration,
maintenance and deployment scripts can still reference durable SQL objects.
Before `0.24.0`, text-only parsing represented such files as `UnnamedScript`.
When multiple physical files were analyzed together, the dependency graph could
merge them into one node because graph identity is name-based.

That behavior destroyed physical-source provenance and could attribute a
reference from one script to another script.

Object-scoped parsing also means one physical source can internally create more
than one fallback `UnnamedScript` scope around durable definitions or `GO`
batches. Those internal scopes are useful for parser ownership, but they must
not become duplicate copies of the same physical source identity.

## Decision

SQL Studio uses `SqlSource` as an input-layer model:

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

A source-aware parse gives fallback script evidence the identity:

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

### One physical source, one fallback Script identity

`parse_source()` returns **at most one fallback `Script` object for a physical
`SqlSource`**.

The lower-level object-scoped parser may materialize several internal
`UnnamedScript` scopes when a file mixes script statements, durable definitions
and `GO` batches. At the source-aware boundary those scopes are aggregated into
one `script:<source_id>` object.

Aggregation preserves evidence conservatively:

- parameters are deduplicated case-insensitively by name;
- variables are deduplicated case-insensitively by name;
- references are deduplicated by database/schema/name/kind;
- temporary-table names are deduplicated case-insensitively;
- `dynamic_sql` is true if any contributing fallback scope contains dynamic SQL.

This aggregation applies **only** to fallback Script scopes. Durable SQL
definitions remain separate `SqlObject` instances and keep their SQL identity.
A view `dbo.Report` located in `sql/views/report.sql` remains `dbo.Report`; it
does not become a source-path node or get merged into the physical Script.

The raw-text `parse()` API retains internal `UnnamedScript` behavior because it
has no physical source identity. Source aggregation belongs specifically to
`parse_source()`.

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
- `RepositoryAnalysisEngine.analyze()` with `SqlSource` inputs

The CLI uses source-aware methods for file and directory analysis.

## Graph semantics

The canonical graph direction does not change:

```text
source -> target
```

For a script file that reads `warroom.ImportColumnDefinition` the graph may
contain:

```text
script:sql/import/003_seed_import_columns_v3.sql
    -> warroom.ImportColumnDefinition
```

Two physical scripts must never collapse merely because neither defines a
schema object. Conversely, multiple internal Script scopes from **one** physical
file must not appear as duplicate physical-source objects.

## Downstream safety

Script nodes remain object type `Script`. Dead Object Detection continues to
consider only supported durable schema-object types, so physical script nodes
do not become deletion candidates.

Repository Analysis source/object inventory therefore has one physical Script
record per source at most, avoiding inflated object counts and duplicate rows.

No Impact, Circular Dependency, Cross Reference or Rule Engine graph direction
is changed by this decision.

## Compatibility

The source-identity contract does not add `source_path` or `source_id` fields to
the public AST or existing serialized schemas.

Raw-text callers retain historical behavior, including internal `UnnamedScript`
scopes. This is deliberate compatibility. Repository/file analysis should use
`SqlSource` to obtain physical identity.

The repository compatibility wrapper keeps its historical text-reader helper
while exposing the source-aware path internally.

## Evidence

The multi-scope aggregation clarification is based on PULSE Repository Analysis
dogfooding documented in `docs/real-repository-validation-pass-4.md`.

## Gate

Future repository-level analysis must preserve physical source identity until
object ownership has been established. New code must not reduce file inputs to
bare SQL strings before dependency analysis when source provenance matters.

A source-aware result must never contain more than one fallback
`script:<source_id>` object for the same `SqlSource`.
