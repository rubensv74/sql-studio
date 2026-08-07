# Roadmap

## Stabilized MVP core

- Repository Engine
- SQL Parser
- Dependency Engine
- Cross Reference Engine
- Impact Analysis Engine
- HTML Impact Report
- Python 3.12 CI baseline
- Repository hygiene and documentation alignment

## Next

1. Circular Dependency Detection
2. Dead Object Detection
3. Static-analysis rule engine consolidation
4. Packaging and installable CLI
5. Reassess profiler and benchmark scope against MVP goals

## Gate for new functionality

New graph-based analyzers must reuse the canonical dependency direction
`source -> target` and include tests that distinguish dependencies from
dependents. No roadmap item is considered complete without CI evidence.
