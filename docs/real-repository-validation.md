# Real Repository Validation — Pass 1

## Purpose

SQL Studio parser changes should be driven by repository evidence rather than speculative grammar expansion. This validation pass exercised the stabilized MVP against representative SQL from a real repository and reduced observed failures into small, non-sensitive regression fixtures.

## Validation source

Repository reviewed: `rubensv74/app_pulse`

Representative source shapes inspected:

- a stored procedure that stages JSON input through `OPENJSON(...)`;
- a stored procedure that combines CTEs, temporary tables, JSON rowsets, durable joins and dynamic SQL;
- a utility catalog/extraction script whose first created table is temporary;
- an idempotent foundation/migration script containing multiple independent durable `CREATE TABLE` definitions.

The SQL Studio regression fixtures are reduced synthetic reproductions. Product/business identifiers and application data are not copied into the test corpus.

## Confirmed defects corrected in 0.20.0

### OPENJSON false dependency

`FROM OPENJSON(...)` and `JOIN OPENJSON(...)` are built-in rowset sources. They are not durable schema objects and must not create graph targets named `OPENJSON`.

The parser now treats `OPENJSON` consistently with the existing `OPENQUERY` / `OPENROWSET` runtime-boundary behavior.

### Temporary CREATE misclassified as durable object

A utility script beginning with `CREATE TABLE #Temp...` could previously make the temporary table the document's primary durable `Table` object.

Temporary table creation is now recorded only in `SqlObject.temporary_tables`. When a utility script has no durable primary definition, later durable references use the existing `Script` fallback rather than promoting the temp table into the dependency graph.

## Regression evidence

Reduced fixtures live under:

`tests/fixtures/real_repository/`

Automated coverage proves:

- JSON rowset sources do not become schema dependencies;
- durable joins around JSON staging remain visible;
- temporary tables remain transient;
- temp-only utility scripts are not typed as durable tables;
- catalog references from a utility script remain statically visible through the Script fallback.

## Architecture decision discovered — not implemented

The validation repository contains migration/foundation files with multiple independent durable schema definitions in one `.sql` file.

The current parser contract is optimized for one primary durable schema object per source file and deliberately collapses document details onto the first durable object. Correct multi-definition support would require explicit ownership of parameters/references/temporary state by statement/object scope rather than the current document-wide accumulation model.

This is therefore **not** treated as a parser bug fix inside 0.20.0. It is an architecture decision because it affects:

- `SqlDocument.objects` semantics;
- reference ownership;
- dependency graph source identity;
- utility/migration script behavior;
- compatibility with the existing one-primary-object repository contract.

No implementation should begin until that object-scope model is selected deliberately.

## Continuing dogfooding rule

Future hardening follows this sequence:

1. identify a concrete failure in a real repository;
2. reduce it to the smallest synthetic fixture that preserves the dependency behavior;
3. classify it as bug, explicit limitation, or architecture decision;
4. fix only non-architectural defects automatically;
5. preserve graph direction and public schemas unless a separate architecture decision authorizes change.
