# SQL Studio CLI

The repository-local CLI is `cli/sqlstudio.py` and targets Python 3.12+.

## Commands

| Command | Purpose |
| --- | --- |
| `new-sprint` | Create a sprint folder and starter README. |
| `new-handoff` | Create a handoff Markdown file. |
| `scan` | Scan a repository and emit its model as JSON. |
| `parse` | Parse one SQL file. |
| `dependencies` | Build the directed SQL dependency graph. |
| `cross-references` | Export direct cross references. |
| `impact` | Find objects that depend on a changed object, transitively. |
| `circular-dependencies` | Detect strongly connected dependency components. |
| `dead-objects` | Find conservative unreferenced-object candidates for review. |

## Shared SQL input rules

Analysis commands accept one or more `.sql` files or directories. Directories are non-recursive unless `-r/--recursive` is supplied. Inputs are deduplicated and processed in deterministic path order. Missing inputs, non-SQL files and directories with no SQL files are handled errors.

## Dependency direction

`source -> target` means `source` depends on `target`. Impact walks incoming dependents; cycle detection analyzes SCCs; dead-object analysis finds supported root components without incoming static references from outside the component.

## `dead-objects`

```text
usage: sqlstudio dead-objects [-h] [-o OUTPUT] [-r] [--compact]
                              [--entry-point OBJECT]
                              paths [paths ...]
```

Examples:

```bash
python cli/sqlstudio.py dead-objects sql/ --recursive
python cli/sqlstudio.py dead-objects sql/ --recursive --entry-point dbo.ApiEntry
python cli/sqlstudio.py dead-objects sql/ --recursive \
  --entry-point dbo.ApiEntry \
  --entry-point reporting.Refresh \
  --output reports/dead-object-candidates.json
```

`--entry-point` is repeatable. It declares a locally defined SQL object that is known to be invoked from outside the analyzed SQL dependency graph. Unknown entry-point names are rejected rather than silently ignored.

### Candidate semantics

A finding is a locally defined component with no incoming static references from another component. Circular islands are grouped into one finding using the Circular Dependency SCC contract.

Supported object types are:

- Stored Procedure
- View
- Function
- Table
- Trigger

Triggers are excluded automatically when they form a root component because their invocation is implicit. `Unknown` nodes and synthetic `Script` nodes are never dead-object candidates.

### JSON schema `1.0`

Representative output:

```json
{
  "schema_version": "1.0",
  "classification": "candidate_only",
  "summary": {
    "defined_object_count": 3,
    "candidate_finding_count": 1,
    "candidate_object_count": 1,
    "excluded_object_count": 1,
    "declared_entry_point_count": 1,
    "dynamic_sql_object_count": 0
  },
  "limitations": {
    "external_usage_may_exist": true,
    "dynamic_sql_may_hide_dependencies": false,
    "safe_to_delete": false
  },
  "entry_points": ["dbo.Entry"],
  "dead_object_candidates": [
    {
      "members": [
        {"name": "dbo.Orphan", "object_type": "View"}
      ],
      "is_circular_component": false,
      "reason": "no_incoming_static_references_from_outside_component",
      "external_usage_possible": true
    }
  ],
  "excluded_objects": [
    {
      "name": "dbo.Entry",
      "object_type": "Stored Procedure",
      "reason": "component_contains_declared_entry_point"
    }
  ]
}
```

The output is intentionally not a deletion recommendation. Application code, jobs, ETL, reporting tools, cross-database callers and unresolved dynamic SQL can use objects without producing an incoming edge in the analyzed repository.

## Other analysis commands

```bash
python cli/sqlstudio.py dependencies sql/ --recursive
python cli/sqlstudio.py cross-references sql/ --recursive
python cli/sqlstudio.py impact sales.Orders sql/ --recursive
python cli/sqlstudio.py circular-dependencies sql/ --recursive
```

JSON analysis commands support `-o/--output`, `-r/--recursive` and `--compact`. `impact` additionally supports `--html FILE`.

## Exit codes

- `0`: successful analysis, including zero findings.
- `1`: handled input, validation, permission or filesystem error.

## Validation

```bash
PYTHONPATH=src python -m unittest discover -s tests -p "test_*.py" -v
```

Target Dead Object Detection with:

```bash
PYTHONPATH=src python -m unittest \
  tests/test_dead_object_engine.py \
  tests/test_dead_object_analyzer.py \
  tests/test_dead_object_serialization.py \
  tests/test_cli_dead_objects.py
```

GitHub Actions also runs compile, import and CLI smoke gates on Python 3.12.
