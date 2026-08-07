# Dead Object Detection Contract

## 1. Purpose

Dead Object Detection identifies SQL schema objects that deserve review because the analyzed repository contains no static incoming reference from another object component.

It does **not** prove that an object is unused and it does **not** authorize deletion.

## 2. Classification

Every result uses:

```text
classification = candidate_only
safe_to_delete = false
```

A candidate may still be used by:

- application or API code;
- SQL Agent jobs or schedulers;
- ETL/orchestration platforms;
- BI/reporting tools;
- another database or repository;
- ad-hoc operational workflows;
- dynamic SQL that cannot be resolved statically.

## 3. Supported objects

The engine analyzes locally defined:

- Stored Procedures
- Views
- Functions
- Tables
- Triggers

Reference-only `Unknown` nodes and synthetic parser `Script` objects are outside the candidate population.

## 4. Graph rule

The canonical graph edge is `source -> target`, meaning `source` depends on `target`.

A component is a candidate when no edge enters it from a different component.

For a normal singleton this is equivalent to having no external static dependents. For a circular island, the SCC is evaluated as a unit so internal references do not hide an otherwise isolated component.

## 5. Entry points and implicit invocation

Use repeatable `--entry-point <qualified_name>` values for SQL objects known to be invoked from outside the analyzed SQL repository.

Entry-point matching is case-insensitive and the canonical graph casing is preserved in output. A declared entry point must resolve to a locally defined supported object; invalid names fail the analysis.

Trigger root components are excluded automatically because trigger activation is implicit and is not represented by a normal incoming dependency edge.

If a root SCC contains an entry point or implicit trigger, the complete component is excluded.

## 6. Dynamic SQL

The analyzer counts parsed SQL objects marked as containing dynamic SQL. The serializer exposes that count and sets `dynamic_sql_may_hide_dependencies=true` when appropriate.

`EXEC sp_executesql ...` is explicitly recognized as dynamic SQL even when `sp_executesql` is parsed as the target of an `EXEC` statement.

Dynamic SQL detection is a warning signal, not complete dynamic dependency resolution.

## 7. Definition metadata

`DependencyResolver` registers all local definitions before resolving references. This two-pass rule ensures that an object referenced before its definition is still recognized as a locally defined typed object rather than remaining `Unknown`.

## 8. JSON contract

Schema `1.0` contains:

- summary counts;
- explicit limitations;
- canonical declared entry points;
- candidate components and member object types;
- whether a finding is a circular SCC;
- exclusion records and reasons.

Output order is deterministic.

## 9. Review procedure

Before deleting any candidate, validate at minimum:

1. application source and API calls;
2. jobs/schedulers and ETL/orchestration;
3. reports/BI datasets;
4. cross-database and linked-server callers;
5. dynamic SQL;
6. operational/ad-hoc dependencies;
7. deployment and rollback scripts.

Dead Object Detection reduces the search space. It does not replace dependency due diligence.
