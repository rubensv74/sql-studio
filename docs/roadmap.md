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
- Static-analysis Rule Engine — shared context, normalized findings and severity gates
- Installable Python packaging — `pyproject.toml`, sdist, wheel and `sqlstudio` console entry point
- Python 3.12 CI baseline with installed-wheel validation
- Repository hygiene, full MIT license and documentation alignment

## Next

1. Reassess profiler and benchmark scope against MVP goals
2. Decide whether release/tag/PyPI automation belongs before or after the profiler/benchmark decision

## Static-analysis gates

All graph analyzers and rules reuse the canonical `source -> target` direction.

Circular Dependency Detection uses one strongly connected component as one circularity finding. Rule `SQL001` adapts this contract with severity `error`.

Dead Object Detection treats a component with no incoming static references from outside the component as a **candidate only**. Rule `SQL002` adapts this contract with severity `warning`; it preserves entry-point, trigger and external-usage safeguards.

The Rule Engine parses inputs once, resolves one dependency graph and shares that context across selected rules. New actionable checks should use stable rule IDs and the normalized Finding/Severity contract instead of adding isolated reporting models by default.

## Packaging gates

The canonical CLI lives inside the installable package. The repository wrapper remains compatibility-only.

A packaging milestone is green only if CI builds sdist/wheel and proves the installed `sqlstudio` command works outside the repository with `PYTHONPATH` cleared.

Publication to PyPI is not implied by installability and requires a separate release decision.

No roadmap item is complete without automated CI evidence and aligned documentation/versioning.
