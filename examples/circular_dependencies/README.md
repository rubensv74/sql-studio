# Circular Dependency Detection example

Use the sibling SQL files to exercise a two-object dependency cycle:

```bash
python cli/sqlstudio.py circular-dependencies examples/circular_dependencies
```

Expected finding: one strongly connected component containing `dbo.CycleA` and
`dbo.CycleB`.
