# Roadmap

## Stabilized MVP static-analysis core

- Repository Engine
- SQL Parser with representative complex T-SQL regression corpus
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
- Performance tooling scope resolved — runtime profiler/benchmark deferred post-MVP and misleading legacy stubs removed

## Next

1. Resolve repository hygiene around `handoff/` versus `handoffs/`
2. Define release/tag/PyPI publication policy
3. Evaluate `main` branch protection before the first tagged release
4. Expand the representative parser corpus when concrete repository syntax exposes a missing dependency pattern

## Parser gates

The parser is dependency-oriented rather than a complete T-SQL compiler. Parser changes must be driven by reduced reproducible fixtures and preserve the public AST unless a separate versioned decision is made.

CTE aliases, temp tables and table variables must not become durable dependency nodes. Dynamic SQL remains uncertainty unless statically resolvable. The canonical graph direction remains `source -> target`.

Current support and limitations are frozen in `docs/parser-support.md`.

## Static-analysis gates

All graph analyzers and rules reuse the canonical `source -> target` direction.

Circular Dependency Detection uses one strongly connected component as one circularity finding. Rule `SQL001` adapts this contract with severity `error`.

Dead Object Detection treats a component with no incoming static references from outside the component as a **candidate only**. Rule `SQL002` adapts this contract with severity `warning`; it preserves entry-point, trigger and external-usage safeguards.

The Rule Engine parses inputs once, resolves one dependency graph and shares that context across selected rules. New actionable checks should use stable rule IDs and the normalized Finding/Severity contract instead of adding isolated reporting models by default.

## Packaging gates

The canonical CLI lives inside the installable package. The repository wrapper remains compatibility-only.

A packaging milestone is green only if CI builds sdist/wheel and proves the installed `sqlstudio` command works outside the repository with `PYTHONPATH` cleared.

Publication to PyPI is not implied by installability and requires a separate release decision.

## Performance tooling gate

Profiler/benchmark concepts are post-MVP. They may re-enter only with an explicit user question, measured/imported metric provenance, reproducibility contract, safety boundary, versioned schema, package integration, tests and non-flaky CI strategy as defined in `docs/performance-tooling-scope.md`.

No roadmap item is complete without automated CI evidence and aligned documentation/versioning.
