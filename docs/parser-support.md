# T-SQL Parser Support Contract

## Purpose

SQL Studio uses a lightweight static parser to discover SQL objects and dependency references. It is intentionally **not** a full T-SQL compiler or semantic engine.

Version `0.18.0` hardens the parser around representative repository patterns that materially affect the dependency graph.

## Supported reference patterns

The regression corpus covers and the parser is expected to preserve:

- `CREATE` and `CREATE OR ALTER` for stored procedures, views, functions, triggers and tables;
- multipart identifiers such as `dbo.TableA` and `OtherDb.sales.TableA`;
- bracket-quoted identifiers, including names containing spaces;
- multiple `FROM` / `JOIN` references in one statement;
- nested/derived-table queries where inner and outer durable sources are collected;
- common table expressions (CTEs), where the CTE alias itself is not emitted as a durable dependency;
- `MERGE [INTO] target USING source` relations;
- `UPDATE alias ... FROM schema.Table AS alias` resolution;
- `APPLY` relation targets when the target is statically named;
- local temporary tables and table variables as transient objects rather than durable graph dependencies;
- direct `EXEC` calls and dynamic execution markers already supported by the execution parser;
- string literals containing escaped/doubled quote characters.

References are deduplicated case-insensitively within one parsed source object while preserving the first observed casing.

## Identifier normalization

Bracket quoting is syntax, not part of the logical object name. For example:

```sql
[OtherDb].[sales].[Order Header]
```

is represented as:

- database: `OtherDb`
- schema: `sales`
- name: `Order Header`

The public `Reference` model remains unchanged.

## CTE and transient-object boundary

CTE names, `#temp` tables and `@table` variables are local query constructs. SQL Studio may record temporary-table presence on `SqlObject.temporary_tables`, but these names must not create durable dependency-graph targets.

References inside a CTE or derived table are still collected when their source objects are statically identifiable.

## Known limitations

The parser remains conservative and does not claim complete T-SQL grammar coverage.

- Dynamic SQL text is not recursively parsed into guaranteed dependencies. It is surfaced as uncertainty.
- Four-part linked-server names do not have a dedicated server field in the current public `Reference` model; the stable graph contract remains database/schema/name oriented.
- Double-quoted identifiers are not promoted to bracket-equivalent identifier semantics because their meaning depends on session settings such as `QUOTED_IDENTIFIER`.
- `OPENQUERY` and `OPENROWSET` are treated as external/runtime boundaries rather than local schema-object dependencies.
- Alias resolution is statement-local and evidence-based; SQL Studio does not perform full name binding or query optimization.
- The current source-file model is optimized for SQL-project style repositories with one primary schema object per `.sql` source. Batches containing multiple independent `CREATE` definitions in one source are not a guaranteed parsing contract.
- Synonyms, linked-server semantics, generated SQL and runtime metadata require separate explicit support before they can be treated as complete dependency evidence.

## Regression corpus

Representative fixtures live under:

`tests/fixtures/tsql_complex/`

The corpus is deliberately small and readable. Every fixture must represent a dependency behavior rather than merely increasing syntax variety. New parser fixes should add or refine a fixture before changing graph semantics.

## Compatibility rule

Parser hardening may improve missing/false references, but it must not redefine the canonical graph direction:

```text
source -> target
```

where source depends on target.

Changes to the public AST, dependency direction or serialized schemas require separate versioned architecture decisions.
