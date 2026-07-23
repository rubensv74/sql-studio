# SQL Studio Architecture

## 1. Architectural principles

SQL Studio is a repository-first Python application for inspecting SQL code, parsing SQL objects, resolving object dependencies, and exporting deterministic machine-readable reports.

The repository is the single source of truth. Runtime components must remain independent from generated handoffs, sprint folders, benchmark artifacts, and documentation assets.

The current architecture follows these rules:

- **Layered flow:** repository input → parser → dependency resolver → graph → serializer/CLI.
- **Small cohesive modules:** each package has one explicit responsibility.
- **Dependency direction:** higher-level orchestration depends on lower-level domain components, never the reverse.
- **Deterministic output:** repository scans and dependency reports use stable ordering.
- **Backward compatibility:** public imports from `sqlstudio` and `sqlstudio.parser` remain the supported API surface.
- **No external runtime dependencies:** the current implementation uses the Python standard library.

## 2. Repository structure

```text
sql-studio/
├── cli/                         # Command-line entry points
│   └── sqlstudio.py
├── core/                        # Project schemas and static configuration
├── docs/                        # Architecture, CLI and roadmap documentation
├── examples/                    # Reproducible SQL and report samples
├── src/sqlstudio/               # Runtime Python package
│   ├── dependencies/            # Dependency Engine
│   ├── parser/                  # Tokenizer, parser, AST and statement parsers
│   ├── models.py                # Repository scan models
│   ├── repository.py            # RepositoryEngine facade
│   └── scanner.py               # SQL repository discovery and classification
└── tests/                       # Unit and integration tests
```

Folders such as `handoffs/`, `sprints/`, `benchmarks/`, and `templates/` support the development process but are not runtime dependencies of `src/sqlstudio`.

## 3. Runtime subsystems

### 3.1 Repository Engine

The Repository Engine discovers SQL files and creates a deterministic repository index.

Main components:

- `RepositoryEngine`: public facade that validates a repository root, invokes the scanner, and exposes dictionary/JSON output.
- `RepositoryScanner`: recursively locates `.sql` files, reads them as UTF-8, and creates `SqlFileEntry` records.
- `SqlClassifier`: classifies scripts as stored procedures, views, functions, or generic scripts using ordered regular-expression rules.
- `ProjectIndex`: aggregate model containing repository metadata and summary counts.

Flow:

```text
Repository path
    ↓
RepositoryEngine
    ↓
RepositoryScanner
    ↓
SqlClassifier
    ↓
ProjectIndex
```

The Repository Engine does not parse SQL syntax or build dependencies. Its responsibility ends at file discovery, classification, and indexing.

### 3.2 SQL Parser

The SQL Parser transforms SQL text into an application-specific abstract syntax model.

Main components:

- `SQLTokenizer`: converts SQL text into tokens while ignoring line and block comments.
- `TokenStream`: provides controlled cursor operations over tokens.
- `SQLParser`: coordinates tokenization, statement splitting, and statement parser execution.
- `ParserContext`: accumulates objects, parameters, variables, references, temporary tables, dynamic SQL, and diagnostics.
- `SqlDocument`: root AST object returned by the parser.
- Statement parsers under `parser/statements/`:
  - `CreationStatementParser`
  - `DeclarationStatementParser`
  - `ExecutionStatementParser`
  - `ReferenceStatementParser`
- `SqlDocumentVisitor`: extension point for read-only AST traversal.

Flow:

```text
SQL text
    ↓
SQLTokenizer
    ↓
TokenStream / statement boundaries
    ↓
Statement parsers
    ↓
ParserContext
    ↓
SqlDocument AST
```

The parser intentionally produces a focused SQL model rather than a complete T-SQL grammar. Unsupported syntax should degrade gracefully and preserve parser stability.

### 3.3 Dependency Engine

The Dependency Engine converts parsed SQL documents into a directed graph of SQL object relationships.

Package:

```text
src/sqlstudio/dependencies/
├── analyzer.py
├── graph.py
├── models.py
├── resolver.py
├── serialization.py
└── __init__.py
```

#### Domain models

`models.py` defines immutable graph entities:

- `DependencyNode`: SQL object name and object type.
- `DependencyEdge`: directed relationship from a source node to a target node.
- `DependencyKind`:
  - `references`
  - `executes`

Nodes and edges are value objects and may therefore be safely stored in sets.

#### Graph

`DependencyGraph` is the in-memory directed graph.

Responsibilities:

- normalize node lookup keys case-insensitively;
- prevent duplicate nodes and edges;
- maintain outgoing and incoming adjacency indexes;
- expose direct dependencies and dependents;
- expose nodes and edges in deterministic order;
- merge additional edges through `extend()`.

Relationship direction is always:

```text
source SQL object → referenced or executed SQL object
```

For example:

```text
reporting.ActiveOrders → sales.Orders
```

#### Resolver

`DependencyResolver` maps parser AST entities into graph entities.

Responsibilities:

- create one source node for each parsed `SqlObject`;
- qualify names as `database.schema.object` when parts are available;
- create placeholder target nodes with type `Unknown` for referenced objects whose definitions are not present;
- map parser reference kind `call` to `DependencyKind.EXECUTES`;
- map all other references to `DependencyKind.REFERENCES`;
- merge one or many `SqlDocument` instances into one graph.

The resolver depends on the parser AST, but the parser has no dependency on the Dependency Engine.

#### Analyzer facade

`DependencyAnalyzer` is the high-level application facade for dependency analysis.

```python
from sqlstudio import DependencyAnalyzer

graph = DependencyAnalyzer().analyze(sql_text)
```

It composes:

```text
SQLParser + DependencyResolver
```

`analyze()` processes one SQL script. `analyze_many()` parses multiple scripts and merges their documents into one graph.

#### Serialization

`DependencyGraphSerializer` converts a graph into deterministic JSON.

The serialized contract contains:

- `schema_version`;
- sorted `nodes`;
- sorted `edges`.

It supports conversion to a dictionary, conversion to JSON text, and direct UTF-8 file writing with automatic parent-directory creation.

### 3.4 Command-line interface

`cli/sqlstudio.py` is the repository-local CLI entry point.

Relevant commands:

- `scan`: repository discovery and classification;
- `parse`: SQL text parsing;
- `dependencies`: dependency graph generation and JSON export.

Dependency command flow:

```text
File/directory arguments
    ↓
SQL file discovery and validation
    ↓
DependencyAnalyzer.analyze_many()
    ↓
DependencyGraph
    ↓
DependencyGraphSerializer
    ↓
stdout or JSON file
```

The CLI is an adapter layer. Business rules belong in `src/sqlstudio`, not in `cli/sqlstudio.py`.

## 4. Dependency rules

Allowed dependency direction:

```text
cli
 ├──> repository engine
 ├──> parser
 └──> dependency engine

DependencyAnalyzer
 ├──> parser
 └──> DependencyResolver

DependencyResolver
 ├──> parser AST
 └──> DependencyGraph / dependency models

DependencyGraphSerializer
 └──> DependencyGraph
```

Forbidden directions:

- parser → dependency engine;
- graph/domain models → parser;
- runtime package → CLI;
- runtime package → tests, handoffs, sprint folders, or documentation;
- repository scanner → dependency engine.

These boundaries prevent circular dependencies and keep each subsystem independently testable.

## 5. Public API

The root package exports the stable high-level API:

```python
from sqlstudio import (
    DependencyAnalyzer,
    DependencyEdge,
    DependencyGraph,
    DependencyKind,
    DependencyNode,
    DependencyResolver,
    RepositoryEngine,
    SQLParser,
)
```

Serialization is available from the dependency package:

```python
from sqlstudio.dependencies import DependencyGraphSerializer
```

New implementations should prefer these public imports rather than importing private module internals.

## 6. Testing strategy

Tests are grouped by subsystem:

```text
tests/test_repository_engine.py
tests/test_sql_parser.py
tests/test_dependency_graph.py
tests/test_dependency_resolver.py
tests/test_dependency_analyzer.py
tests/test_dependency_serialization.py
tests/test_cli_dependencies.py
```

Expected coverage responsibilities:

- domain validation and duplicate handling;
- deterministic node/edge ordering;
- incoming and outgoing graph navigation;
- AST-to-graph mapping;
- qualified SQL names;
- `references` versus `executes` relationships;
- multi-document graph merging;
- stable JSON schema and UTF-8 output;
- CLI file discovery, recursive mode, output files, and error handling;
- parser and repository regression protection.

Run the complete suite from the repository root:

```bash
PYTHONPATH=src python -m unittest discover -s tests -p "test_*.py"
```

## 7. Extension guidelines

Future dependency features must extend the existing subsystem rather than bypass it.

Examples:

- transitive dependency traversal belongs in `DependencyGraph` or a dedicated graph service;
- cycle detection belongs in the dependency package, operating on `DependencyGraph`;
- additional relationship types belong in `DependencyKind`;
- richer object-type resolution belongs in `DependencyResolver`;
- additional export formats belong beside `serialization.py`;
- repository-wide orchestration should compose `RepositoryEngine`, `SQLParser`, and `DependencyAnalyzer` in a separate application service.

Any architectural change that reverses the dependency directions defined above requires explicit technical justification and approval before implementation.
