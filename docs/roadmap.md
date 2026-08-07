# Roadmap

## Stabilized MVP static-analysis core

- Repository Engine
- SQL Parser
- Dependency Engine
- Cross Reference Engine
- Impact Analysis Engine
- HTML Impact Report
- Circular Dependency Detection
- Dead Object Detection — conservative candidate classification
- Python 3.12 CI baseline
- Repository hygiene and documentation alignment

## Next

1. Static-analysis Rule Engine Consolidation
2. Packaging and installable CLI
3. Reassess profiler and benchmark scope against MVP goals

## Graph-analysis gates

All graph analyzers reuse the canonical `source -> target` direction.

Circular Dependency Detection uses one strongly connected component as one circularity finding.

Dead Object Detection treats a component with no incoming static references from outside the component as a **candidate only**. Known external entry points can be declared explicitly; trigger roots are excluded; external callers and unresolved dynamic SQL prevent any claim that a candidate is safe to delete.

No roadmap item is complete without automated CI evidence and aligned documentation/versioning.
