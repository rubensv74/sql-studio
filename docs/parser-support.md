# T-SQL Parser Support Contract

## Purpose

SQL Studio uses a lightweight static parser to discover SQL objects and dependency references. It is intentionally **not** a full T-SQL compiler or semantic engine.

Version `0.22.0` extends the object-scoped parser contract with DDL dependency evidence from inline foreign keys observed during real-repository dogfooding. One source file may contain multiple durable SQL-object definitions, and each emitted `SqlObject` owns only the evidence observed in its active scope.

## Supported reference and definition patterns

The regression corpus covers and the parser is expected to preserve:

- `CREATE` and `CREATE OR ALTER` for stored procedures, views, functions, triggers and tables;
- multiple durable definitions in one `.sql` source when object/batch ownership can be established;
- guarded durable DDL such as `IF OBJECT_ID(...) IS NULL BEGIN CREATE TABLE ... END`;
- inline `FOREIGN KEY (...) REFERENCES schema.Table (...)` dependencies owned by the defining table;
- permission syntax such as `GRANT REFERENCES ON ...` without false dependency emission;
- standalone `GO` lines as client batch/object-scope boundaries;
- stored-procedure parameters with or without surrounding parentheses;
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
- direct `EXEC` calls and dynamic execution markers;
- string literals containing escaped/doubled quote characters.

References are deduplicated case-insensitively **within each parsed object scope** while preserving the first observed casing.

## Object-scope ownership

`SqlDocument.objects` may contain multiple durable objects from one source file. Parser evidence is not accumulated globally and then attached to the first object.

The active scope owns parameters, variables, references/calls, temporary tables and dynamic-SQL evidence. The scope is finalized when a new durable definition starts, a standalone `GO` batch boundary is reached, or the document ends.

See `docs/object-scoped-parser.md` for the architecture contract.

## DDL foreign-key evidence

A foreign-key target is a durable structural dependency:

```sql
CREATE TABLE warroom.Child
(
    ParentId bigint NOT NULL,
    CONSTRAINT FK_Child_Parent
        FOREIGN KEY (ParentId)
        REFERENCES warroom.Parent (ParentId)
);
```

SQL Studio records:

```text
warroom.Child -> warroom.Parent
```

The parser does **not** treat every occurrence of `REFERENCES` as an object relation. A `REFERENCES` target is collected only when `FOREIGN KEY` evidence exists earlier in the same statement. This avoids permission syntax such as `GRANT REFERENCES ON ...` becoming a false target named `ON`.

This milestone guarantees inline foreign-key dependencies in object-owned DDL. Standalone `ALTER TABLE ... ADD CONSTRAINT ... FOREIGN KEY` ownership requires reliable identification of the altered durable source object and is not silently approximated as a schema-object edge.

## Identifier normalization

Bracket quoting is syntax, not part of the logical object name. For example `[OtherDb].[sales].[Order Header]` is represented as database `OtherDb`, schema `sales`, name `Order Header`. The public `Reference` model remains unchanged.

## CTE and transient-object boundary

CTE names, `#temp` / `##temp` tables and `@table` variables are local execution constructs. SQL Studio may record temporary-table presence on `SqlObject.temporary_tables`, but these names must not create durable dependency-graph nodes or targets.

A utility script whose only `CREATE TABLE` statements are temporary remains a `Script`; the temporary table must not become a durable table object. References inside a CTE or derived table are still collected when their source objects are statically identifiable.

## Built-in rowset boundary

`OPENJSON`, `OPENQUERY` and `OPENROWSET` can syntactically appear after `FROM` / `JOIN`, but they are not local schema objects. SQL Studio suppresses them as dependency targets while retaining durable relations around them.

The suppression list is evidence-driven. New built-in table-valued or rowset sources are added only when a reduced real-repository fixture demonstrates a false dependency.

## Known limitations

The parser remains conservative and does not claim complete T-SQL grammar coverage.

- Dynamic SQL text is not recursively parsed into guaranteed dependencies. It is surfaced as uncertainty.
- Four-part linked-server names do not have a dedicated server field in the current public `Reference` model; the stable graph contract remains database/schema/name oriented.
- Double-quoted identifiers are not promoted to bracket-equivalent identifier semantics because their meaning depends on session settings such as `QUOTED_IDENTIFIER`.
- `OPENQUERY`, `OPENROWSET` and `OPENJSON` are treated as external/runtime or built-in rowset boundaries rather than local schema-object dependencies.
- Alias resolution is statement-local and evidence-based; SQL Studio does not perform full name binding or query optimization.
- Permanent runtime DDL encountered inside an already active stored module is not promoted to a second top-level repository definition.
- Standalone `ALTER TABLE` DDL is not yet promoted to a durable source-object scope.
- Multi-definition support is guaranteed only where source structure provides reliable ownership boundaries; syntax that cannot be assigned to the correct object remains unsupported rather than being guessed.
- Synonyms, linked-server semantics, generated SQL and runtime metadata require separate explicit support before they can be treated as complete dependency evidence.

## Regression corpus

Representative fixtures live under:

- `tests/fixtures/tsql_complex/` — dependency-oriented complex T-SQL patterns;
- `tests/fixtures/real_repository/` — reduced synthetic cases derived from real-repository failures;
- `tests/fixtures/object_scopes/` — multi-definition, batch-boundary, evidence-ownership and DDL foreign-key cases.

Every fixture must represent dependency or ownership behavior rather than merely increasing syntax variety.

## Compatibility rule

Parser hardening may improve missing/false references, but it must not redefine the canonical graph direction:

```text
source -> target
```

where source depends on target.

Changes to the public AST, dependency direction or serialized schemas require separate versioned architecture decisions. Object-scoped ownership remains frozen by the `0.21.0` architecture contract.
