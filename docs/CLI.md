# SQL Studio CLI

The repository-local CLI is `cli/sqlstudio.py`.

## Requirements

- Python 3.12 or later.
- Run commands from the repository root.
- No installation step is currently required.
- SQL files are read as UTF-8; undecodable characters are ignored.

## General usage

```bash
python cli/sqlstudio.py --help
python cli/sqlstudio.py <command> --help
```

Available commands:

| Command | Purpose |
| --- | --- |
| `new-sprint` | Create a sprint folder and starter README. |
| `new-handoff` | Create a handoff Markdown file. |
| `scan` | Scan a repository and emit its model as JSON. |
| `parse` | Parse one SQL file and emit detected SQL structures as JSON. |
| `dependencies` | Build the directed SQL dependency graph. |
| `cross-references` | Export direct cross references. |
| `impact` | Find objects that depend on a selected object, transitively. |
| `circular-dependencies` | Detect strongly connected dependency components and self-references. |

## Dependency direction

The CLI uses the same contract as the package:

```text
source -> target
```

means `source` depends on `target`.

Consequently, `dependencies` describes the graph itself, `impact ROOT` walks
incoming dependents, and `circular-dependencies` analyzes closed loops in the
canonical directed graph.

## `new-sprint`

```bash
python cli/sqlstudio.py new-sprint baseline-example
```

Creates `sprints/<name>/README.md`.

## `new-handoff`

```bash
python cli/sqlstudio.py new-handoff baseline-example
```

Creates `handoffs/<name>.md`.

## `scan`

```bash
python cli/sqlstudio.py scan .
python cli/sqlstudio.py scan path/to/repository > reports/repository.json
```

## `parse`

```bash
python cli/sqlstudio.py parse examples/sample_procedure.sql
```

The command prints parser output as JSON, including detected objects,
parameters, variables, references, temporary tables and dynamic SQL fragments.

## Shared SQL input rules

`dependencies`, `cross-references`, `impact` and `circular-dependencies` accept
one or more SQL files or directories.

- Directories are non-recursive by default.
- Use `-r` / `--recursive` for nested directories.
- Duplicate files are removed by resolved path.
- Inputs are processed in deterministic path order.
- A non-`.sql` file is rejected.
- Missing inputs or directories without SQL files return a handled error.

## `dependencies`

```text
usage: sqlstudio dependencies [-h] [-o OUTPUT] [-r] [--compact]
                              paths [paths ...]
```

Examples:

```bash
python cli/sqlstudio.py dependencies examples/sample_procedure.sql
python cli/sqlstudio.py dependencies sql/ --recursive
python cli/sqlstudio.py dependencies sql/ --recursive --output reports/dependencies.json
python cli/sqlstudio.py dependencies sql/ --recursive --compact
```

The JSON schema contains stable node and edge collections. An edge such as:

```json
{
  "source": "reporting.ActiveOrders",
  "target": "sales.Orders",
  "kind": "references"
}
```

means `reporting.ActiveOrders` depends on `sales.Orders`.

## `cross-references`

```text
usage: sqlstudio cross-references [-h] [-o OUTPUT] [-r] [--compact]
                                  paths [paths ...]
```

Examples:

```bash
python cli/sqlstudio.py cross-references examples/sample_procedure.sql
python cli/sqlstudio.py cross-references sql/ --recursive
python cli/sqlstudio.py cross-references sql/ --recursive --output reports/cross-references.json
```

The report distinguishes standard reads/references from procedure executions
according to the dependency kind produced by the parser and resolver.

## `impact`

```text
usage: sqlstudio impact [-h] [-o OUTPUT] [-r] [--html HTML] [--compact]
                        root_object paths [paths ...]
```

`root_object` is the SQL object assumed to be changed.

Examples:

```bash
python cli/sqlstudio.py impact sys.objects examples/sample_procedure.sql
python cli/sqlstudio.py impact sales.Orders sql/ --recursive --output reports/orders-impact.json
python cli/sqlstudio.py impact sales.Orders sql/ --recursive --html reports/orders-impact.html
```

### JSON output

Impact JSON schema `1.0` is deliberately flat:

```json
{
  "schema_version": "1.0",
  "root_object": "sales.Orders",
  "impacted_objects": [
    "dbo.ActiveOrders",
    "sales.Orders"
  ]
}
```

The root is always present in `impacted_objects`. The serializer sorts the flat
collection for stable machine-readable output.

The hierarchical tree is currently an in-memory/HTML concern and is not part of
schema `1.0`. Adding it to JSON requires a new schema version.

### HTML output

`--html FILE` writes a self-contained report containing the root object, total
impact, direct impacts, indirect impacts and a navigable impact tree.

## `circular-dependencies`

```text
usage: sqlstudio circular-dependencies [-h] [-o OUTPUT] [-r] [--compact]
                                       paths [paths ...]
```

Examples:

```bash
python cli/sqlstudio.py circular-dependencies sql/ --recursive
python cli/sqlstudio.py circular-dependencies sql/ --recursive --output reports/cycles.json
python cli/sqlstudio.py circular-dependencies a.sql b.sql --compact
```

The command reports one finding per strongly connected component (SCC), rather
than enumerating every possible cyclic path. A one-object SCC is reported only
when the object has a self-reference.

Representative schema `1.0`:

```json
{
  "schema_version": "1.0",
  "summary": {
    "cycle_count": 1,
    "object_count": 2
  },
  "circular_dependencies": [
    {
      "members": ["dbo.A", "dbo.B"],
      "is_self_reference": false,
      "edges": [
        {"source": "dbo.A", "target": "dbo.B", "kind": "references"},
        {"source": "dbo.B", "target": "dbo.A", "kind": "references"}
      ]
    }
  ]
}
```

The ordering of findings, members and internal edges is deterministic. Object
identity is case-insensitive while output preserves the canonical name already
stored in the dependency graph.

## Output options

For JSON-producing analysis commands:

| Option | Meaning |
| --- | --- |
| `-o`, `--output FILE` | Write JSON to a file instead of stdout. |
| `-r`, `--recursive` | Search supplied directories recursively. |
| `--compact` | Emit JSON without indentation. |

`impact` additionally supports `--html FILE` for a self-contained HTML report.
Parent directories are created for report destinations.

## Exit codes

- `0`: success, including a valid analysis that finds no circular dependencies.
- `1`: handled input, validation, permission or file-system error.

Handled errors are written to stderr.

## Validation

Run the complete suite:

```bash
PYTHONPATH=src python -m unittest discover -s tests -p "test_*.py" -v
```

Circular Dependency Detection can be targeted with:

```bash
PYTHONPATH=src python -m unittest \
  tests/test_circular_dependency_engine.py \
  tests/test_circular_dependency_analyzer.py \
  tests/test_circular_dependency_serialization.py \
  tests/test_cli_circular_dependencies.py
```

The GitHub Actions workflow runs the full suite on Python 3.12 and also performs
compile, import and CLI smoke checks.
