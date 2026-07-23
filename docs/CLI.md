# SQL Studio CLI

The command-line interface is provided by `cli/sqlstudio.py` and is designed to be executed from the repository root.

## Requirements

- Python 3.10 or later.
- No installation step is required for repository-local execution.
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
| `scan` | Scan a repository and emit its repository model as JSON. |
| `parse` | Parse one SQL file and emit the parser result as JSON. |
| `dependencies` | Build and export a SQL object dependency graph. |

## `new-sprint`

Creates `sprints/<name>/README.md`.

```bash
python cli/sqlstudio.py new-sprint Sprint011
```

## `new-handoff`

Creates `handoffs/<name>.md`.

```bash
python cli/sqlstudio.py new-handoff sprint-010-complete
```

## `scan`

Scans a repository folder with `RepositoryEngine` and prints JSON to standard output.

```bash
python cli/sqlstudio.py scan .
python cli/sqlstudio.py scan path/to/sql-repository > reports/repository.json
```

## `parse`

Parses one SQL file and prints the detected SQL objects, parameters, variables, references, temporary tables, and dynamic SQL fragments.

```bash
python cli/sqlstudio.py parse examples/sample_procedure.sql
```

The command writes JSON to standard output, so it can be redirected:

```bash
python cli/sqlstudio.py parse examples/sample_procedure.sql \
  > reports/sample_procedure.parse.json
```

## `dependencies`

Builds a dependency graph from one or more SQL files or directories.

```text
usage: sqlstudio dependencies [-h] [-o OUTPUT] [-r] [--compact]
                              paths [paths ...]
```

### Inputs

Each positional `path` may be:

- a `.sql` file;
- a directory containing `.sql` files;
- one of several files and directories supplied in the same command.

Directory scans are non-recursive by default. Use `--recursive` to include nested folders.

Duplicate files are removed using their resolved path, and files are processed in a deterministic order.

### Options

| Option | Meaning |
| --- | --- |
| `-o`, `--output FILE` | Write the JSON graph to `FILE` instead of standard output. Parent directories are created automatically. |
| `-r`, `--recursive` | Search supplied directories recursively for `.sql` files. |
| `--compact` | Emit compact JSON without indentation. |

### Analyze one file

```bash
python cli/sqlstudio.py dependencies examples/sample_procedure.sql
```

### Analyze several files

```bash
python cli/sqlstudio.py dependencies \
  sql/views/active_orders.sql \
  sql/procedures/process_orders.sql
```

### Analyze a directory

```bash
python cli/sqlstudio.py dependencies sql/
```

Only `.sql` files located directly in `sql/` are included.

### Analyze a directory recursively

```bash
python cli/sqlstudio.py dependencies sql/ --recursive
```

### Write the graph to a report file

```bash
python cli/sqlstudio.py dependencies sql/ \
  --recursive \
  --output reports/dependencies.json
```

When `--output` is used, the CLI prints the destination path after writing the report.

### Emit compact JSON

```bash
python cli/sqlstudio.py dependencies sql/ --recursive --compact
```

Compact output is useful for automated pipelines or when minimizing report size.

### Redirect standard output

Without `--output`, the graph is printed to standard output:

```bash
python cli/sqlstudio.py dependencies sql/ --recursive \
  > reports/dependencies.json
```

Prefer `--output` when possible because it creates missing parent directories automatically.

## Dependency graph format

The JSON document contains a schema version plus stable, sorted node and edge collections.

Representative structure:

```json
{
  "schema_version": "1.0",
  "nodes": [
    {
      "name": "dbo.activeorders",
      "kind": "view"
    },
    {
      "name": "sales.orders",
      "kind": "unknown"
    }
  ],
  "edges": [
    {
      "source": "dbo.activeorders",
      "target": "sales.orders",
      "kind": "references"
    }
  ]
}
```

Names and kinds reflect the normalized values produced by the parser and dependency engine.

## Reproducible example

Create two SQL files:

```sql
-- sql/tables/orders.sql
CREATE TABLE sales.Orders
(
    OrderId int NOT NULL
);
```

```sql
-- sql/views/active_orders.sql
CREATE VIEW reporting.ActiveOrders
AS
SELECT OrderId
FROM sales.Orders;
```

Generate the report:

```bash
python cli/sqlstudio.py dependencies sql/ \
  --recursive \
  --output reports/dependencies.json
```

The resulting graph contains nodes for the created objects and an edge from `reporting.ActiveOrders` to `sales.Orders`.

## Exit codes and validation errors

The CLI returns:

- `0` when the command completes successfully;
- `1` when an input path is missing, a file is not SQL, no SQL files are found, a destination cannot be written, or another handled file-system/value error occurs.

Examples of invalid input:

```bash
python cli/sqlstudio.py dependencies missing.sql
python cli/sqlstudio.py dependencies README.md
python cli/sqlstudio.py dependencies empty-folder/
```

Errors are written to standard error, which allows normal shell and CI error handling.

## Running the CLI tests

From the repository root:

```bash
PYTHONPATH=src python -m unittest tests/test_cli_dependencies.py
```

Run the complete Dependency Engine test set with:

```bash
PYTHONPATH=src python -m unittest \
  tests/test_dependency_graph.py \
  tests/test_dependency_resolver.py \
  tests/test_dependency_analyzer.py \
  tests/test_dependency_serialization.py \
  tests/test_cli_dependencies.py
```
