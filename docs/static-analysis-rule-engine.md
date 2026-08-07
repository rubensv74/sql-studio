# Static-analysis Rule Engine

## Purpose

The Rule Engine provides one normalized contract for actionable static-analysis findings without replacing SQL Studio's structural analysis services.

Dependency, Cross Reference and Impact Analysis remain services. Circular Dependency Detection and Dead Object Detection are exposed as rules because they produce findings that can be classified, counted and gated.

## Shared execution model

One `StaticAnalysisAnalyzer` run performs:

1. parse every SQL input once;
2. build one canonical `DependencyGraph`;
3. create one `RuleContext` containing parsed documents, graph and declared entry points;
4. execute the selected rules against that shared context;
5. normalize their output into `Finding`, `RuleResult` and `StaticAnalysisResult`.

Rules must not reparse the repository or redefine dependency direction.

The graph contract remains:

```text
source -> target
```

meaning `source` depends on `target`.

## Rule contract

Every rule exposes:

- stable `rule_id`;
- title and description;
- default `Severity`;
- `evaluate(RuleContext) -> RuleResult`.

Rule IDs are case-insensitive at the API/CLI boundary and canonicalized to uppercase. Duplicate rule IDs are rejected.

### Severity levels

The schema defines three ordered severities:

1. `info`
2. `warning`
3. `error`

They are intentionally small and stable. Rule-specific business meaning belongs in the finding message/properties, not in additional ad-hoc severity names.

## Built-in rules

### SQL001 — Circular dependency

- Severity: `error`.
- Adapter over `CircularDependencyEngine`.
- One finding represents one strongly connected component or one self-reference.
- Finding properties include `is_self_reference` and `internal_edge_count`.

### SQL002 — Dead object candidate

- Severity: `warning`.
- Adapter over `DeadObjectEngine`.
- Findings remain review candidates only.
- Declared entry points and trigger safeguards remain active.
- Finding properties include `classification=candidate_only`, `external_usage_may_exist=true` and `safe_to_delete=false`.

The Rule Engine does not weaken the Dead Object safety contract.

## JSON schema 1.0

The consolidated serializer returns:

- `summary`: rule/finding counts, severity counts and shared graph/parser metrics;
- `context`: entry points and the `static_analysis_only` marker;
- `rules`: one execution record per rule;
- `findings`: normalized findings with rule ID, severity, affected objects and typed properties.

Representative output:

```json
{
  "schema_version": "1.0",
  "summary": {
    "rule_count": 2,
    "finding_count": 1,
    "error_count": 0,
    "warning_count": 1,
    "info_count": 0
  },
  "context": {
    "entry_points": ["dbo.Entry"],
    "static_analysis_only": true
  },
  "findings": [
    {
      "rule_id": "SQL002",
      "severity": "warning",
      "title": "Dead object candidate",
      "objects": ["dbo.Orphan"],
      "properties": {
        "classification": "candidate_only",
        "safe_to_delete": false
      }
    }
  ]
}
```

Additional summary fields and rule execution metadata are part of schema `1.0`; consumers should ignore unknown additive fields.

## CLI gating

`sqlstudio analyze` runs all built-in rules by default.

- `--rule RULE_ID` is repeatable and selects rules explicitly.
- `--entry-point OBJECT` is repeatable and is shared with rules that need external-entry knowledge.
- `--fail-on info|warning|error` returns exit code `2` when a finding at or above the selected threshold exists.

Exit code `2` means **analysis completed and a configured quality gate was breached**. It is distinct from exit code `1`, which means input/validation/filesystem failure.

The JSON report is still emitted when `--fail-on` returns `2`, allowing CI systems to retain the diagnostic artifact.

## Compatibility

The existing `circular-dependencies` and `dead-objects` commands and their JSON schemas remain supported. Rule Engine consolidation is additive: consumers can migrate to `analyze` when they need a unified report or CI gate.

## Extension rule

New actionable static-analysis checks should normally be implemented as `StaticAnalysisRule` implementations using the shared context. A new rule must include:

- a stable, documented rule ID;
- explicit default severity;
- deterministic findings;
- regression tests;
- serializer/CLI coverage where appropriate;
- no duplicate parsing or alternate dependency-graph semantics.
