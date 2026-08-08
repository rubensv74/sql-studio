# Unified Repository Analysis

## Status

Approved architecture for SQL Studio `0.25.0`.

The canonical product-level repository analysis is a **versioned master result**. JSON and HTML are two representations of the same analysis result; HTML is not the source of truth.

## Goals

One repository analysis run should answer, from one shared parse/graph context:

- what physical SQL sources exist in the supplied analysis set;
- what durable SQL objects or script scopes were discovered in each source;
- what dependencies exist and in which canonical direction;
- which objects have the most incoming dependents;
- which circular dependency components exist;
- which dead-object candidates require human review;
- which normalized static-analysis findings exist by severity;
- where dynamic SQL creates static-analysis uncertainty;
- which physical source produced each locally defined object.

## Non-goals for 0.25.0

- no GUI framework or server;
- no persistence/database;
- no precomputed impact report for every object;
- no change to Impact JSON schema `1.0`;
- no change to `SqlDocument`, `SqlObject`, `Reference` or dependency graph schemas;
- no claim that dead-object candidates are safe to delete;
- no runtime SQL Server profiling;
- no PyPI publication.

## Architecture

```text
SqlSource[]
    |
    v
SQLParser.parse_source()        once per source
    |
    v
SqlDocument[]
    |
    v
DependencyResolver             one canonical graph
    |
    +-----------------------+
    |                       |
    v                       v
RuleContext              repository inventory
    |                       |
    +----------+------------+
               |
               v
RepositoryAnalysisEngine
    |
    v
RepositoryAnalysisResult
    |
    +--> RepositoryAnalysisSerializer --> JSON schema 1.0
    |
    +--> RepositoryAnalysisReportGenerator --> self-contained HTML
```

Parsing must not be repeated by the report engine. Specialized graph algorithms may operate over the already resolved graph.

## Canonical graph semantics

The existing dependency direction remains unchanged:

```text
source -> target
```

The source depends on the target.

Therefore:

- outgoing edges answer what an object uses;
- incoming edges answer what uses an object;
- an object's `dependent_count` is the number of incoming dependents;
- high dependent count is a useful repository-centrality signal but is not itself a finding or severity.

## Source provenance

`SqlSource.source_id` is the physical-source identity.

During one analysis run, the engine keeps the source and its parsed `SqlDocument` paired. This pairing is used to build source/object inventory records.

Durable objects keep their SQL names. Script-only scopes keep the `script:<source_id>` identity introduced in `0.24.0`.

No source field is added to the SQL AST in `0.25.0`.

## Master Python result

`RepositoryAnalysisResult` is a new product-level model. It may compose existing stable analysis models rather than duplicate their algorithms.

It must expose enough information for both machine and human views:

- source inventory;
- locally defined object inventory with source identity;
- canonical dependency graph;
- circular dependency components;
- dead-object result including exclusions and candidate-only semantics;
- normalized static-analysis result;
- entry points.

Summary metrics should be derived from this result rather than maintained independently.

## JSON schema 1.0

The repository-analysis serializer owns a new schema namespace/version. Existing serializers are not modified.

Top-level shape:

```json
{
  "schema_version": "1.0",
  "summary": {},
  "sources": [],
  "objects": [],
  "dependencies": {
    "nodes": [],
    "edges": []
  },
  "cycles": [],
  "dead_object_candidates": [],
  "dead_object_exclusions": [],
  "rules": [],
  "findings": [],
  "uncertainty": {},
  "context": {}
}
```

### Summary

Schema `1.0` summary includes at least:

- `source_count`;
- `parsed_object_count`;
- `durable_object_count`;
- `script_object_count`;
- `graph_node_count`;
- `dependency_edge_count`;
- `circular_component_count`;
- `dead_object_candidate_count`;
- `finding_count`;
- `error_count`;
- `warning_count`;
- `info_count`;
- `dynamic_sql_object_count`.

### Source records

Each source record contains:

- `source_id`;
- optional `path` when supplied by the caller;
- ordered local `objects` discovered in that source.

### Object records

Each locally defined object record contains:

- `name`;
- `object_type`;
- `source_id`;
- `dynamic_sql`;
- `dependencies`;
- `dependents`;
- `dependency_count`;
- `dependent_count`.

Reference-only external/unknown graph nodes remain present in the dependency graph but are not invented as locally defined repository objects.

### Uncertainty

Dynamic SQL remains an explicit uncertainty boundary. Schema `1.0` reports:

- `dynamic_sql_object_count`;
- names of locally defined objects carrying dynamic-SQL evidence;
- `static_analysis_only: true`.

The report must not convert uncertainty into false dependency certainty.

## HTML report

The HTML report is self-contained and generated exclusively from `RepositoryAnalysisResult`.

Initial sections:

1. executive summary;
2. repository inventory;
3. dependency overview;
4. key objects ranked by incoming dependents;
5. circular dependencies;
6. dead-object candidates and exclusions/safety warning;
7. findings by severity;
8. dynamic-SQL uncertainty;
9. object explorer/table with source, dependencies and dependents;
10. source traceability.

No external JavaScript or CSS dependency is required.

## CLI

`0.25.0` adds one product-level command:

```bash
sqlstudio repository-analysis <paths...>
```

Default output is repository-analysis JSON `1.0` to stdout.

Supported options:

```text
-r / --recursive
-o / --output <json-file>
--html <html-file>
--compact
--entry-point <object>    repeatable
```

When both JSON output and `--html` are supplied, both representations are produced from the same in-memory `RepositoryAnalysisResult`.

Existing commands remain supported and keep their current schemas.

## Determinism

The master result and JSON serialization must be deterministic for the same ordered source contents and configuration.

Schema `1.0` deliberately omits run timestamps, host paths inferred from environment, machine names, Git metadata and other volatile execution metadata. A future provenance schema may add such data through an explicit versioned decision.

## Compatibility

`0.25.0` is additive:

- no existing command is removed;
- no existing analyzer method is removed;
- no existing JSON schema is silently extended;
- `SqlSource` remains the canonical physical-source input;
- graph direction remains `source -> target`;
- Dead Object Detection remains candidate-only;
- Impact Analysis remains a specialized on-demand capability.

## Acceptance gates

The milestone is complete only when automated tests prove:

1. every supplied `SqlSource` is parsed once by the master analyzer;
2. source/object provenance is correct for durable and Script scopes;
3. graph metrics equal the canonical dependency graph;
4. cycles and dead-object candidates match their existing engines;
5. rule findings match the shared rule engine context;
6. object dependencies/dependents use canonical graph direction;
7. JSON schema `1.0` is deterministic;
8. HTML is self-contained, escaped and includes all required sections;
9. CLI can emit JSON, HTML or both from one analysis run;
10. the installed wheel passes a repository-analysis smoke test outside the checkout.
