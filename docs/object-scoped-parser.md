# SQL Studio — Object-Scoped Parser Architecture

## Decision

Version `0.21.0` adopts an **object-scoped parser model** for SQL source files that contain more than one durable schema-object definition.

The public AST remains unchanged:

```text
SqlDocument
  -> objects: list[SqlObject]
```

The change is internal ownership semantics. Each active `SqlObject` owns only the parser evidence observed while its scope is active.

## Scope-owned evidence

The following data belongs to the active object scope:

- parameters;
- local variables;
- durable references;
- execution/call references;
- temporary tables;
- dynamic-SQL evidence.

When a new durable object starts, a standalone `GO` batch boundary is reached, or the document ends, the active scope is materialized as an immutable `SqlObject` and its mutable evidence is reset before another scope begins.

## Batch semantics

`GO` is treated as a client batch separator only when it appears by itself on a source line. An identifier named `GO`, for example `dbo.[GO]`, remains an ordinary SQL identifier.

This allows SQL Studio to model SQL-project and migration-style files such as:

```sql
CREATE VIEW dbo.A AS SELECT * FROM dbo.SourceA;
GO
CREATE VIEW dbo.B AS SELECT * FROM dbo.SourceB;
GO
```

as two independent objects with independent dependency ownership.

## Guarded DDL

Repository migration files frequently wrap durable DDL in guards:

```sql
IF OBJECT_ID(N'dbo.A', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.A (...);
END;
GO
```

Creation discovery therefore does not require `CREATE` to be the first token of the semicolon-delimited statement. Dynamic SQL literals remain literals and are not promoted to durable definitions.

## Script scope

Statements that produce evidence outside a durable object can still be represented by the existing synthetic `Script` object. Script scope is finalized at the same batch/document boundaries and never becomes a durable schema-object candidate in Dead Object Detection.

## Compatibility

This architecture deliberately does **not** change:

- `SqlObject` or `SqlDocument` public fields;
- `Reference` public fields;
- dependency direction (`source -> target`);
- `DependencyResolver` semantics;
- Cross Reference semantics;
- Impact Analysis traversal;
- Circular Dependency semantics;
- Dead Object candidate-only safety contract;
- Rule Engine finding schemas;
- CLI command names or exit codes.

Existing one-object-per-file repositories remain valid inputs.

## Runtime DDL boundary

A permanent `CREATE TABLE` encountered inside an already active stored module is treated as runtime implementation behavior rather than as a second top-level repository definition. Temporary `#`/`##` tables remain transient scope evidence.

This prevents procedure-body DDL from stealing ownership from its containing module.

## Validation contract

Regression coverage must prove all of the following:

1. two durable objects in one source file are both emitted;
2. parameters and variables do not leak between objects;
3. references do not leak between objects;
4. temporary tables do not leak between objects;
5. dynamic-SQL evidence does not leak between objects;
6. dependency-graph edges use each durable object as the correct source;
7. guarded migration DDL is recognized;
8. standalone `GO` ends a scope while an identifier named `GO` does not.

Fixtures live under `tests/fixtures/object_scopes/`.

## Architecture rule

Future parser work must preserve **evidence ownership before syntax coverage**. A syntax extension that cannot assign evidence to the correct object scope must remain unsupported rather than emit a misleading dependency graph.
