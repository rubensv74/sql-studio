# Circular Dependency Detection

## Purpose

Detect closed dependency loops in the canonical SQL Studio dependency graph.

## Graph contract

Edges keep the established direction:

```text
source -> target
```

where `source` depends on `target`.

## Finding contract

One circular dependency finding represents one strongly connected component
(SCC), not every possible cyclic path inside that component.

A finding is emitted when:

- the SCC contains two or more SQL objects; or
- a one-object SCC contains a self-referencing edge.

Each finding contains:

- deterministically sorted member names;
- whether the finding is a self-reference;
- all dependency edges whose source and target are both members of the SCC.

SQL object identity is case-insensitive. Output preserves the canonical casing
stored by `DependencyGraph`.

## Algorithm

`CircularDependencyEngine` uses Tarjan's strongly connected components
algorithm. This provides linear complexity in graph size, O(V + E), and avoids
the potentially exponential cost and duplicate output produced by enumerating
all simple cyclic paths.

## JSON schema 1.0

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

A valid analysis with no circular dependencies returns an empty
`circular_dependencies` array and exits successfully.

## CLI

```bash
python cli/sqlstudio.py circular-dependencies sql/ --recursive
python cli/sqlstudio.py circular-dependencies sql/ --recursive --output reports/cycles.json
```

## Validation cases

The milestone is covered for:

- acyclic graphs;
- two-object cycles;
- multi-hop cycles;
- self-references;
- disconnected components;
- case-insensitive object identity;
- deterministic ordering;
- multi-file SQL analysis;
- JSON serialization;
- CLI stdout/file output and handled input errors.
