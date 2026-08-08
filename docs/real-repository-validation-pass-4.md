# Real Repository Validation — Pass 4

## Scope

This pass validates the public SQL Studio `0.25.0` Repository Analysis against a fixed real PULSE SQL corpus, then verifies the `0.26.0` hardening branch against the exact same PULSE commit.

Validation corpus:

- repository: `rubensv74/app_pulse`
- commit: `919ea5ed59c856469f873d9a766479fac3fa8391`
- analyzed path: `sql/`
- physical SQL sources: 5

The first run installed the published `sql_studio-0.25.0-py3-none-any.whl` from the GitHub Release rather than executing a SQL Studio development checkout.

## Baseline evidence — released 0.25.0

Repository Analysis completed successfully and generated both JSON schema `1.0` and self-contained HTML.

Observed summary:

| Metric | 0.25.0 |
| --- | ---: |
| Sources | 5 |
| Parsed object records | 14 |
| Durable objects | 9 |
| Script objects | 5 |
| Graph nodes | 35 |
| Dependency edges | 33 |
| Circular components | 0 |
| Dead-object candidate components | 5 |
| Static-analysis findings | 5 |
| Errors | 0 |
| Warnings | 5 |
| Dynamic-SQL objects | 2 |
| Unknown graph nodes | 23 |

The five SQL002 warnings were:

- `warroom.ImportAudit`;
- `warroom.ImportBatchRow`;
- `warroom.usp_CompletePunchExportBatch`;
- `warroom.usp_ExportProjectPunchesExtended_Pivoted`;
- `warroom.usp_RegisterPunchExportSnapshot`.

These remain candidate-only findings and may represent externally invoked application/flow entry points.

## Defect 1 — duplicate physical Script records

`sql/import/001_import_foundations.sql` contains durable table definitions plus statements/batches that belong to fallback Script scopes.

The object-scoped parser correctly isolated those internal scopes, but `SQLParser.parse_source()` renamed every fallback `UnnamedScript` scope to the same physical identity:

```text
script:pulse/sql/import/001_import_foundations.sql
```

The Repository Analysis inventory therefore listed that identical Script object three times. The dependency graph itself is name-keyed and collapsed those identities, but the local object/source inventory did not.

Consequences:

- `parsed_object_count` was inflated from 12 unique local identities to 14 records;
- `script_object_count` was inflated from 3 physical Script identities to 5 records;
- the key-object table repeated the same physical Script row;
- source traceability was noisier than the actual repository model.

### Correction

Object-scoped internal ownership remains unchanged.

At the source-aware boundary, `parse_source()` now aggregates all fallback Script scopes from one physical `SqlSource` into exactly one `script:<source_id>` object. Durable objects stay independent and unchanged.

Aggregated Script evidence is conservative:

- parameters deduplicate case-insensitively by name;
- variables deduplicate case-insensitively by name;
- references deduplicate by database/schema/name/kind;
- temporary tables deduplicate case-insensitively;
- `dynamic_sql` is true when any contributing Script scope contains dynamic-SQL evidence.

The historical raw-text `parse()` contract is unchanged and may still expose internal `UnnamedScript` scopes because it has no physical source identity.

## Defect 2 — transient UPDATE alias promoted to Unknown

The real export procedure contains this shape:

```sql
UPDATE eb
SET ...
FROM #ExportBase eb
CROSS APPLY (...);
```

The parser already suppresses `#ExportBase` as a durable dependency. However, because the transient source was discarded before its alias was retained, later `UPDATE eb` fell back to treating `eb` as a durable relation name.

This created a false graph node:

```text
Unknown: eb
```

### Correction

Relation parsing now remembers aliases whose source is known to be transient/non-durable:

- temporary tables;
- table variables;
- CTEs;
- built-in rowset boundaries such as `OPENJSON`, `OPENQUERY` and `OPENROWSET`.

When an `UPDATE` target resolves to one of those aliases, the target is suppressed instead of being emitted as a durable relation.

Durable alias-targeted updates keep the existing behavior and continue resolving to their real relation.

## Corrected dogfood evidence

The hardening branch was installed and executed against the exact same fixed PULSE commit. Assertions were made directly in GitHub Actions.

| Metric | 0.25.0 | Corrected | Delta |
| --- | ---: | ---: | ---: |
| Sources | 5 | 5 | 0 |
| Parsed object records | 14 | 12 | -2 |
| Script objects | 5 | 3 | -2 |
| Graph nodes | 35 | 34 | -1 |
| Dependency edges | 33 | 32 | -1 |
| Unknown nodes | 23 | 22 | -1 |
| Findings | 5 | 5 | 0 |

The corrected run proves:

- `001_import_foundations.sql` has exactly one physical Script identity;
- `eb` no longer exists in the Unknown node set;
- the false `eb` edge disappears;
- the five SQL002 candidates remain unchanged;
- no cycle or severity behavior changes;
- the report becomes more faithful without hiding real external/system dependencies.

## Interpretation of remaining Unknown nodes

The remaining Unknown nodes are not automatically defects. They include legitimate dependencies not defined inside the five-file validation corpus, such as:

- application database objects under `dbo`;
- `warroom.CustomFieldDef`, `warroom.CustomFieldValue`, `warroom.PunchComment`;
- SQL Server `sys.*` catalog objects;
- `sys.sp_executesql` execution evidence.

The analysis must not relabel these as locally defined objects without source evidence.

## Regression corpus

Synthetic fixtures were added for both defects:

- `tests/fixtures/real_repository/multi_scope_physical_script.sql`;
- `tests/fixtures/real_repository/update_temp_alias.sql`.

The regression suite proves one physical fallback Script identity per `SqlSource`, evidence aggregation, preservation of durable definitions and suppression of transient UPDATE aliases.

## Safety and compatibility

This pass does not redefine architecture:

- object-scoped parser ownership remains the internal parsing model;
- `SqlSource` remains the physical identity boundary;
- `SqlDocument`, `SqlObject` and `Reference` fields do not change;
- Repository Analysis JSON remains schema `1.0`;
- dependency direction remains `source -> target`;
- Dead Object Detection remains candidate-only;
- dynamic SQL remains uncertainty.

The changes improve fidelity within the contracts already approved in `0.21.0`, `0.24.0` and `0.25.0`.
