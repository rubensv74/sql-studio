# SQL Studio CLI

SQL Studio targets Python 3.12+ and installs the console command `sqlstudio`.

The canonical implementation lives in `src/sqlstudio/cli.py`. `cli/sqlstudio.py` remains a repository-checkout compatibility wrapper and reexports the same callable surface used by existing tests/consumers.

## Installation

```bash
python -m pip install .
sqlstudio --version
```

For editable development installs:

```bash
python -m pip install -e .
```

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
| `repository-analysis` | Produce the unified repository result as JSON and optional HTML. |

## Shared SQL input rules

Analysis commands accept one or more `.sql` files or directories. Directories are non-recursive unless `-r/--recursive` is supplied. Inputs are deduplicated and processed in deterministic path order. Missing inputs, non-SQL files and directories with no SQL files are handled errors.

File/directory analysis preserves `SqlSource.source_id`, so standalone scripts retain distinct physical identity instead of collapsing into a shared `UnnamedScript` node.

## Dependency direction

`source -> target` means `source` depends on `target`. Impact walks incoming dependents; cycle detection analyzes SCCs; dead-object analysis finds supported root components without incoming static references from outside the component. The Rule Engine and Repository Analysis reuse this graph and do not define a second dependency direction.

## `repository-analysis`

```text
usage: sqlstudio repository-analysis [-h] [-o OUTPUT] [-r] [--html HTML]
                                     [--compact] [--entry-point OBJECT]
                                     paths [paths ...]
```

Examples:

```bash
sqlstudio repository-analysis sql/ --recursive
sqlstudio repository-analysis sql/ --recursive --entry-point dbo.ApiEntry
sqlstudio repository-analysis sql/ --recursive \
  --output reports/repository-analysis.json \
  --html reports/repository-analysis.html
```

The command parses each physical SQL source once, resolves one dependency graph and reuses that context for cycles, dead-object candidates and static-analysis rules.

Default output is Repository Analysis JSON schema `1.0` on stdout. `--output` writes that JSON to a file. `--html` additionally writes a self-contained human-readable HTML report from the same in-memory `RepositoryAnalysisResult`.

Schema `1.0` includes:

- executive summary metrics;
- physical source inventory and source-to-object provenance;
- locally defined objects with direct dependencies and dependents;
- canonical graph nodes and edges;
- circular components;
- dead-object candidates and exclusions;
- normalized rule metadata and findings;
- dynamic-SQL uncertainty;
- entry-point and graph-direction context.

The unified report is additive: specialized commands and their existing schemas remain supported.

## `analyze`

```text
usage: sqlstudio analyze [-h] [-o OUTPUT] [-r] [--compact]
                         [--entry-point OBJECT] [--rule RULE_ID]
                         [--fail-on SEVERITY]
                         paths [paths ...]
```

Examples:

```bash
sqlstudio analyze sql/ --recursive
sqlstudio analyze sql/ --recursive --entry-point dbo.ApiEntry
sqlstudio analyze sql/ --recursive --rule SQL001
sqlstudio analyze sql/ --recursive \
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

### `--fail-on`

`--fail-on info|warning|error` turns findings into an optional CI quality gate. Severity order is `info < warning < error`.

The report is still written/printed before exit code `2` is returned.

## `dead-objects`

```text
usage: sqlstudio dead-objects [-h] [-o OUTPUT] [-r] [--compact]
                              [--entry-point OBJECT]
                              paths [paths ...]
```

`--entry-point` declares a locally defined SQL object known to be invoked from outside the analyzed SQL graph. The command retains Dead Object JSON schema `1.0`.

A finding is a candidate only; it is not deletion proof. Circular islands are grouped using the SCC contract, triggers are excluded as implicit entry objects, and `Unknown`/synthetic `Script` nodes are never dead-object candidates.

## Other analysis commands

```bash
sqlstudio dependencies sql/ --recursive
sqlstudio cross-references sql/ --recursive
sqlstudio impact sales.Orders sql/ --recursive
sqlstudio circular-dependencies sql/ --recursive
sqlstudio dead-objects sql/ --recursive --entry-point dbo.ApiEntry
```

JSON analysis commands support `-o/--output`, `-r/--recursive` and `--compact`. `impact` additionally supports `--html FILE`.

## Version

```bash
sqlstudio --version
```

The output is `sqlstudio <package-version>` and is derived from `sqlstudio.__version__`.

## Compatibility wrapper

Existing repository-local automation can continue to use:

```bash
python cli/sqlstudio.py repository-analysis sql/ --recursive
```

The wrapper imports and reexports the canonical `sqlstudio.cli` callables; business logic is not duplicated there.

## Exit codes

- `0`: successful analysis, including zero findings or findings below an optional `--fail-on` threshold.
- `1`: handled input, validation, permission or filesystem error.
- `2`: `analyze` completed successfully but a finding met/exceeded the requested `--fail-on` severity.

## Validation

```bash
PYTHONPATH=src python -m unittest discover -s tests -p "test_*.py" -v
python -m build
```

GitHub Actions also installs the generated wheel and invokes `sqlstudio` from `/tmp` with `PYTHONPATH` empty. Repository-analysis smoke coverage proves the installed distribution can produce its versioned JSON contract and self-contained HTML report outside the checkout.
