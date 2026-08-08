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
- Canonical handoff repository path — `handoffs/`; legacy singular duplicate removed
- Performance tooling scope resolved — runtime profiler/benchmark deferred post-MVP and misleading legacy stubs removed
- GitHub-only release policy — successful `main` CI creates immutable SemVer tag + GitHub Release with wheel/sdist assets
- First controlled GitHub Release `v0.19.0` verified with wheel and sdist assets
- Real-repository validation pass 1 — JSON rowset and temporary-object false positives reduced into regression fixtures and corrected in `0.20.0`

## Next

1. Protect `main` using the documented CI-gated branch policy when repository-administration access is available
2. Resolve the architecture decision for multiple independent durable `CREATE` definitions in one `.sql` source
3. Continue real-repository dogfooding and parser hardening from concrete failures after that boundary is resolved
4. Design the unified Repository Analysis Report only after real-repository graph fidelity is adequate
5. Revisit PyPI publication only through a separate explicit decision

## Parser gates

The parser is dependency-oriented rather than a complete T-SQL compiler. Parser changes must be driven by reduced reproducible fixtures and preserve the public AST unless a separate versioned decision is made.

CTE aliases, temp tables and table variables must not become durable dependency nodes. `OPENJSON`, `OPENQUERY` and `OPENROWSET` are built-in/runtime rowset boundaries rather than local schema objects. Dynamic SQL remains uncertainty unless statically resolvable. The canonical graph direction remains `source -> target`.

Current support and limitations are frozen in `docs/parser-support.md`. Real-repository evidence and the first discovered architecture boundary are recorded in `docs/real-repository-validation.md`.

### Open architecture boundary: multi-definition source files

Real-repository validation confirmed migration/foundation scripts that contain several independent durable schema-object definitions in one `.sql` file.

The current parser accumulates parameters, references, transient state and dynamic-SQL evidence at document scope and then exposes one primary durable source object. Correct multi-definition support therefore requires an explicit object-scope/reference-ownership model; it must not be approximated by simply returning every encountered `CREATE` token.

No implementation of that model begins without a deliberate architecture decision.

## Repository hygiene gate

`handoffs/` is the canonical handoff-note directory. The legacy singular `handoff/` path must not be recreated unless a separate migration decision explicitly supersedes this contract.

The `new-handoff` command remains compatible and writes to `handoffs/`.

## Static-analysis gates

All graph analyzers and rules reuse the canonical `source -> target` direction.

Circular Dependency Detection uses one strongly connected component as one circularity finding. Rule `SQL001` adapts this contract with severity `error`.

Dead Object Detection treats a component with no incoming static references from outside the component as a **candidate only**. Rule `SQL002` adapts this contract with severity `warning`; it preserves entry-point, trigger and external-usage safeguards.

The Rule Engine parses inputs once, resolves one dependency graph and shares that context across selected rules. New actionable checks should use stable rule IDs and the normalized Finding/Severity contract instead of adding isolated reporting models by default.

## Packaging gates

The canonical CLI lives inside the installable package. The repository wrapper remains compatibility-only.

A packaging milestone is green only if CI builds sdist/wheel and proves the installed `sqlstudio` command works outside the repository with `PYTHONPATH` cleared.

PyPI publication is not implied by installability or by a GitHub Release.

## Release gates

The current release channel is GitHub Releases only, as defined in `docs/release-policy.md`.

A stable release may be created only after the `CI` workflow succeeds on `main`. The release workflow checks out the exact validated commit, validates the canonical package version and compatibility mirror, enforces immutable `vMAJOR.MINOR.PATCH` tag identity, builds the wheel/sdist and creates the GitHub Release when it does not already exist.

The release workflow must not contain PyPI upload credentials or publication steps. PyPI requires a later explicit product decision.

## Branch-protection gate

`main` should require the `test` CI job, pull-request integration, conversation resolution, up-to-date branches, and blocking of force pushes/deletion. The reproducible target configuration is defined in `docs/branch-protection.md`.

## Performance tooling gate

Profiler/benchmark concepts are post-MVP. They may re-enter only with an explicit user question, measured/imported metric provenance, reproducibility contract, safety boundary, versioned schema, package integration, tests and non-flaky CI strategy as defined in `docs/performance-tooling-scope.md`.

No roadmap item is complete without automated CI evidence and aligned documentation/versioning.
