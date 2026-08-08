# T-SQL Parser Support Contract

## Purpose

SQL Studio uses a lightweight static parser to discover SQL objects and dependency references. It is intentionally **not** a full T-SQL compiler or semantic engine.

Version `0.20.0` extends the representative parser contract with evidence gathered by running the stabilized MVP against real repository SQL. Parser growth remains driven by concrete dependency failures rather than syntax breadth for its own sake.

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
- `CREATE TABLE #temp` / `CREATE TABLE ##temp` as transient creation rather than durable table definitions;
- built-in rowset/runtime sources `OPENJSON`, `OPENQUERY` and `OPENROWSET` as non-schema dependencies;
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

CTE names, `#temp` / `##temp` tables and `@table` variables are local execution constructs. SQL Studio may record temporary-table presence on `SqlObject.temporary_tables`, but these names must not create durable dependency-graph nodes or targets.

A utility script whose only `CREATE TABLE` statements are temporary remains a `Script`; the temporary table must not become the document's durable primary object.

References inside a CTE or derived table are still collected when their source objects are statically identifiable.

## Built-in rowset boundary

`OPENJSON`, `OPENQUERY` and `OPENROWSET` can syntactically appear after `FROM` / `JOIN`, but they are not local schema objects. SQL Studio therefore suppresses them as dependency targets while retaining durable relations around them.

The suppression list is evidence-driven. New built-in table-valued or rowset sources are added only when a reduced real-repository fixture demonstrates a false dependency.

## Known limitations

The parser remains conservative and does not claim complete T-SQL grammar coverage.

- Dynamic SQL text is not recursively parsed into guaranteed dependencies. It is surfaced as uncertainty.
- Four-part linked-server names do not have a dedicated server field in the current public `Reference` model; the stable graph contract remains database/schema/name oriented.
- Double-quoted identifiers are not promoted to bracket-equivalent identifier semantics because their meaning depends on session settings such as `QUOTED_IDENTIFIER`.
- `OPENQUERY`, `OPENROWSET` and `OPENJSON` are treated as external/runtime or built-in rowset boundaries rather than local schema-object dependencies.
- Alias resolution is statement-local and evidence-based; SQL Studio does not perform full name binding or query optimization.
- The current source-file model is optimized for SQL-project style repositories with one primary durable schema object per `.sql` source. Batches containing multiple independent durable `CREATE` definitions in one source are not a guaranteed parsing contract.
- Real-repository validation confirmed that multi-definition migration/foundation scripts exist. Correct support requires a deliberate object-scope/reference-ownership architecture decision and is not silently approximated in `0.20.0`.
- Synonyms, linked-server semantics, generated SQL and runtime metadata require separate explicit support before they can be treated as complete dependency evidence.

## Regression corpus

Representative fixtures live under:

- `tests/fixtures/tsql_complex/` — dependency-oriented complex T-SQL patterns;
- `tests/fixtures/real_repository/` — reduced synthetic cases derived from real-repository failures.

The corpus is deliberately small and readable. Every fixture must represent a dependency behavior rather than merely increasing syntax variety. New parser fixes should add or refine a fixture before changing graph semantics.

The first dogfooding pass and its architecture boundary are documented in `docs/real-repository-validation.md`.

## Compatibility rule

Parser hardening may improve missing/false references, but it must not redefine the canonical graph direction:

```text
source -> target
```

where source depends on target.

Changes to the public AST, dependency direction, object-scope ownership or serialized schemas require separate versioned architecture decisions.
