# Roadmap

## Stabilized MVP core

- Repository Engine
- SQL Parser
- Dependency Engine
- Cross Reference Engine
- Impact Analysis Engine
- HTML Impact Report
- Circular Dependency Detection
- Python 3.12 CI baseline
- Repository hygiene and documentation alignment

## Next

1. Dead Object Detection
2. Static-analysis rule engine consolidation
3. Packaging and installable CLI
4. Reassess profiler and benchmark scope against MVP goals

## Gate for new functionality

New graph-based analyzers must reuse the canonical dependency direction
`source -> target` and include tests that distinguish dependencies from
dependents. No roadmap item is considered complete without CI evidence.

Circular Dependency Detection defines one finding as a strongly connected
component (SCC). Self-referencing objects are also circular findings. This
contract avoids enumerating exponentially many equivalent cycle paths.
