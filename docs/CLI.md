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
| `analyze` | Run consolidated static-analysis rules and emit normalized findings. |

## Shared SQL input rules

Analysis commands accept one or more `.sql` files or directories. Directories are non-recursive unless `-r/--recursive` is supplied. Inputs are deduplicated and processed in deterministic path order. Missing inputs, non-SQL files and directories with no SQL files are handled errors.

## Dependency direction

`source -> target` means `source` depends on `target`. Impact walks incoming dependents; cycle detection analyzes SCCs; dead-object analysis finds supported root components without incoming static references from outside the component. The Rule Engine reuses this graph and does not define a second dependency direction.

## `analyze`

```text
usage: sqlstudio analyze [-h] [-o OUTPUT] [-r] [--compact]
                         [--entry-point OBJECT] [--rule RULE_ID]
                         [--fail-on SEVERITY]
                         paths [paths ...]
```

Examples:

```bash
# Run all built-in rules
python cli/sqlstudio.py analyze sql/ --recursive

# Supply known external entry points for rules such as SQL002
python cli/sqlstudio.py analyze sql/ --recursive --entry-point dbo.ApiEntry

# Run only circular-dependency detection through the common rule contract
python cli/sqlstudio.py analyze sql/ --recursive --rule SQL001

# Fail a CI gate on warnings or errors while still emitting JSON
python cli/sqlstudio.py analyze sql/ --recursive \
  --entry-point dbo.ApiEntry \
  --fail-on warning \
  --output reports/static-analysis.json
```

### Built-in rule IDs

| Rule | Severity | Meaning |
| --- | --- | --- |
| `SQL001` | `error` | Circular dependency component or self-reference. |
| `SQL002` | `warning` | Dead-object candidate requiring human review. |

`--rule` is repeatable. Rule IDs are case-insensitive and unknown IDs return a handled validation error.

`--entry-point` is repeatable. Entry points are shared through the Rule Context; currently SQL002 uses them to suppress roots known to be invoked externally.

### Consolidated JSON schema `1.0`

The report contains:

- `summary`: rule/finding counts, severity counts and shared parser/graph metrics;
- `context`: entry points and a static-analysis-only marker;
- `rules`: execution metadata for every selected rule;
- `findings`: normalized rule ID, severity, title/message, affected objects and properties.

Example fragment:

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
  "findings": [
    {
      "rule_id": "SQL002",
      "severity": "warning",
      "objects": ["dbo.Orphan"],
      "properties": {
        "classification": "candidate_only",
        "safe_to_delete": false
      }
    }
  ]
}
```

### `--fail-on`

`--fail-on info|warning|error` turns findings into an optional CI quality gate.

Severity order is `info < warning < error`. For example, `--fail-on warning` returns `2` for warnings or errors, while `--fail-on error` ignores warning-only findings.

The report is still written/printed before exit code `2` is returned.

## `dead-objects`

```text
usage: sqlstudio dead-objects [-h] [-o OUTPUT] [-r] [--compact]
                              [--entry-point OBJECT]
                              paths [paths ...]
```

`--entry-point` declares a locally defined SQL object known to be invoked from outside the analyzed SQL graph. The command remains a dedicated compatibility surface and retains Dead Object JSON schema `1.0`.

A finding is a candidate only; it is not deletion proof. Circular islands are grouped using the SCC contract, triggers are excluded as implicit entry objects, and `Unknown`/synthetic `Script` nodes are never dead-object candidates.

## Other analysis commands

```bash
python cli/sqlstudio.py dependencies sql/ --recursive
python cli/sqlstudio.py cross-references sql/ --recursive
python cli/sqlstudio.py impact sales.Orders sql/ --recursive
python cli/sqlstudio.py circular-dependencies sql/ --recursive
python cli/sqlstudio.py dead-objects sql/ --recursive --entry-point dbo.ApiEntry
```

JSON analysis commands support `-o/--output`, `-r/--recursive` and `--compact`. `impact` additionally supports `--html FILE`.

## Exit codes

- `0`: successful analysis, including zero findings or findings below an optional `--fail-on` threshold.
- `1`: handled input, validation, permission or filesystem error.
- `2`: `analyze` completed successfully but a finding met/exceeded the requested `--fail-on` severity.

## Validation

```bash
PYTHONPATH=src python -m unittest discover -s tests -p "test_*.py" -v
```

Target Rule Engine consolidation with:

```bash
PYTHONPATH=src python -m unittest \
  tests/test_static_analysis_rule_engine.py \
  tests/test_static_analysis_analyzer.py \
  tests/test_static_analysis_serialization.py \
  tests/test_cli_static_analysis.py
```

GitHub Actions also runs compile, import and CLI smoke gates on Python 3.12, including real SQL001/SQL002 findings and the exit-code-2 severity gate.
