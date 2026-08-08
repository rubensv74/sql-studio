# T-SQL Parser Support Contract

## Purpose

SQL Studio uses a lightweight static parser to discover SQL objects and dependency references. It is intentionally **not** a full T-SQL compiler or semantic engine.

The parser combines the `0.21.0` object-scoped ownership architecture, `0.22.0` DDL foreign-key dependency evidence, `0.23.0` real procedure/function signature handling and the `0.26.0` PULSE hardening for physical Script aggregation and transient UPDATE aliases.

## Supported reference and definition patterns

The regression corpus covers and the parser is expected to preserve:

- `CREATE` and `CREATE OR ALTER` for stored procedures, views, functions, triggers and tables;
- multiple durable definitions in one `.sql` source when object/batch ownership can be established;
- guarded durable DDL such as `IF OBJECT_ID(...) IS NULL BEGIN CREATE TABLE ... END`;
- inline `FOREIGN KEY (...) REFERENCES schema.Table (...)` dependencies owned by the defining table;
- permission syntax such as `GRANT REFERENCES ON ...` without false dependency emission;
- standalone `GO` lines as client batch/object-scope boundaries;
- stored-procedure parameters with or without surrounding parentheses;
- parameterized datatypes such as `nvarchar(320)`, `decimal(18,4)` and `datetime2(3)` without prematurely ending or splitting the parameter list;
- parameter defaults and `OUTPUT` / `OUT` markers;
- input-normalization `SET @Parameter = ...` statements without duplicating parameters as local variables;
- multipart identifiers such as `dbo.TableA` and `OtherDb.sales.TableA`;
- bracket-quoted identifiers, including names containing spaces;
- multiple `FROM` / `JOIN` references in one statement;
- nested/derived-table queries where inner and outer durable sources are collected;
- common table expressions (CTEs), where the CTE alias itself is not emitted as a durable dependency;
- `MERGE [INTO] target USING source` relations;
- `UPDATE alias ... FROM schema.Table AS alias` resolution for durable sources;
- `UPDATE alias ... FROM #temp/@table/CTE AS alias` suppression when the alias resolves to a transient source;
- `APPLY` relation targets when the target is statically named;
- local temporary tables and table variables as transient objects rather than durable graph dependencies;
- `CREATE TABLE #temp` / `CREATE TABLE ##temp` as transient creation rather than durable table definitions;
- built-in rowset/runtime sources `OPENJSON`, `OPENQUERY` and `OPENROWSET` as non-schema dependencies;
- direct `EXEC` calls and dynamic execution markers;
- string literals containing escaped/doubled quote characters.

References are deduplicated case-insensitively **within each parsed object scope** while preserving the first observed casing. Parameters and local variables are also separated case-insensitively within their owning scope.

## Object-scope ownership

`SqlDocument.objects` may contain multiple durable objects from one source file. Parser evidence is not accumulated globally and then attached to the first object.

The active scope owns parameters, variables, references/calls, temporary tables and dynamic-SQL evidence. The scope is finalized when a new durable definition starts, a standalone `GO` batch boundary is reached, or the document ends.

Raw-text `SQLParser.parse()` preserves these internal ownership scopes. The source-aware `parse_source()` layer may aggregate multiple fallback `UnnamedScript` scopes into one physical `script:<source_id>` identity; durable object scopes are never merged by that aggregation.

See `docs/object-scoped-parser.md` and `docs/sql-source-identity.md` for the architecture contracts.

## Procedure and function parameters

SQL Server stored procedures commonly omit outer parentheses around the parameter list, while functions commonly include them. Datatypes can also contain their own nested parentheses and commas:

```sql
CREATE PROCEDURE dbo.P
    @Name nvarchar(320),
    @Amount decimal(18,4) = 0,
    @At datetime2(3) = NULL
AS
BEGIN
    ...
END;
```

The parser distinguishes datatype nesting from the optional outer parameter-list boundary. Inner `)` tokens and commas therefore do not terminate or split the module signature.

A procedure parameter that is later assigned through `SET` remains a parameter only. Real local variables introduced through `DECLARE` remain in `SqlObject.variables`.

See `docs/real-repository-validation-pass-3.md` for the evidence and reduced fixture.

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

SQL Studio records `warroom.Child -> warroom.Parent`.

The parser does **not** treat every occurrence of `REFERENCES` as an object relation. A `REFERENCES` target is collected only when `FOREIGN KEY` evidence exists earlier in the same statement. This avoids permission syntax such as `GRANT REFERENCES ON ...` becoming a false target named `ON`.

Inline foreign-key dependencies in object-owned DDL are guaranteed. Standalone `ALTER TABLE ... ADD CONSTRAINT ... FOREIGN KEY` ownership requires reliable identification of the altered durable source object and is not silently approximated as a schema-object edge.

## Identifier normalization

Bracket quoting is syntax, not part of the logical object name. For example `[OtherDb].[sales].[Order Header]` is represented as database `OtherDb`, schema `sales`, name `Order Header`. The public `Reference` model remains unchanged.

## CTE, transient-object and alias boundary

CTE names, `#temp` / `##temp` tables and `@table` variables are local execution constructs. SQL Studio may record temporary-table presence on `SqlObject.temporary_tables`, but these names must not create durable dependency-graph nodes or targets.

A utility script whose only `CREATE TABLE` statements are temporary remains a `Script`; the temporary table must not become a durable table object. References inside a CTE or derived table are still collected when their source objects are statically identifiable.

Alias binding is statement-local. If a durable source is known, `UPDATE alias ... FROM dbo.Table AS alias` resolves to the durable table. If the source is known to be transient or a built-in rowset, the alias is remembered only as non-durable evidence so `UPDATE alias` cannot fall back to a false `Unknown` graph node.

This behavior is backed by the PULSE `UPDATE eb ... FROM #ExportBase eb` regression recorded in `docs/real-repository-validation-pass-4.md`.

## Built-in rowset boundary

`OPENJSON`, `OPENQUERY` and `OPENROWSET` can syntactically appear after `FROM` / `JOIN`, but they are not local schema objects. SQL Studio suppresses them as dependency targets while retaining durable relations around them.

Aliases bound to those built-in rowsets are also non-durable for UPDATE-target resolution.

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
- Parameter datatype metadata currently records the logical datatype identifier rather than reconstructing full size/precision text; parentheses are parsed for boundary correctness.
- Multi-definition support is guaranteed only where source structure provides reliable ownership boundaries; syntax that cannot be assigned to the correct object remains unsupported rather than being guessed.
- Synonyms, linked-server semantics, generated SQL and runtime metadata require separate explicit support before they can be treated as complete dependency evidence.

## Regression corpus

Representative fixtures live under:

- `tests/fixtures/tsql_complex/` — dependency-oriented complex T-SQL patterns;
- `tests/fixtures/real_repository/` — reduced synthetic cases derived from real-repository failures, including physical Script aggregation and transient UPDATE aliases;
- `tests/fixtures/object_scopes/` — multi-definition, batch-boundary, evidence-ownership, DDL foreign-key and real procedure-parameter cases.

Every fixture must represent dependency or ownership behavior rather than merely increasing syntax variety.

## Compatibility rule

Parser hardening may improve missing/false references, parameter metadata and variable classification, but it must not redefine the canonical graph direction:

```text
source -> target
```

where source depends on target.

Changes to the public AST, dependency direction or serialized schemas require separate versioned architecture decisions. Object-scoped ownership remains frozen by the `0.21.0` architecture contract; physical source identity remains frozen by `docs/sql-source-identity.md`.
