# Roadmap

## Stabilized MVP static-analysis core

- Repository Engine
- SQL Parser with representative complex T-SQL regression corpus
- Object-scoped multi-definition parser ownership — multiple durable objects per source with isolated evidence
- Physical SQL source identity — source-aware repository analysis prevents independent scripts collapsing into `UnnamedScript`
- DDL foreign-key dependency evidence for inline `FOREIGN KEY ... REFERENCES` constraints
- Real SQL Server procedure/function parameter parsing across parameterized datatypes
- Parameter/local-variable classification without `SET @Parameter` duplication
- Dependency Engine
- Cross Reference Engine
- Impact Analysis Engine
- HTML Impact Report
- Circular Dependency Detection
- Dead Object Detection — conservative candidate classification
- Static-analysis Rule Engine — shared context, normalized findings and severity gates
- Unified Repository Analysis — one master result, JSON schema `1.0` and self-contained HTML report
- Source/object traceability and key-object ranking by incoming dependents
- Installable Python packaging — `pyproject.toml`, sdist, wheel and `sqlstudio` console entry point
- Python 3.12 CI baseline with installed-wheel validation
- Repository hygiene, full MIT license and documentation alignment
- Canonical handoff repository path — `handoffs/`; legacy singular duplicate removed
- Performance tooling scope resolved — runtime profiler/benchmark deferred post-MVP and misleading legacy stubs removed
- GitHub-only release policy — successful `main` CI creates immutable SemVer tag + GitHub Release with wheel/sdist assets
- Real-repository validation pass 1 — JSON rowset and temporary-object false positives corrected in `0.20.0`
- Multi-definition architecture decision resolved in `0.21.0` through object-scoped evidence ownership
- Real-repository validation pass 2 — inline foreign-key targets promoted to dependency edges in `0.22.0` without treating permission `REFERENCES` as schema dependencies
- Real-repository validation pass 3 — parameterized datatype boundaries and parameter/local-variable classification corrected in `0.23.0`
- Physical-source identity decision resolved in `0.24.0` through `SqlSource` while preserving the public SQL AST
- Unified repository-analysis architecture resolved in `0.25.0` through `RepositoryAnalysisResult` while preserving all specialized schemas

## Next

1. Dogfood the unified Repository Analysis against representative real repositories and review report usefulness, not only parser fidelity
2. Expand parser coverage only from concrete dependency/ownership failures found during that dogfooding
3. Evaluate standalone `ALTER TABLE ... FOREIGN KEY` source ownership only when representative repository evidence requires it; do not emit Script-sourced schema edges as a shortcut
4. Evaluate the next product surface (for example richer navigation or a GUI) only after the `0.25.0` report contract has proven stable
5. Protect `main` using the documented CI-gated branch policy when repository-administration access is available
6. Revisit PyPI publication only through a separate explicit decision

## Unified repository-analysis gate

`RepositoryAnalysisResult` is the canonical product-level repository result. JSON and HTML must be generated from the same in-memory result; HTML must not re-run analysis or define independent semantics.

The master engine parses every `SqlSource` once, resolves one dependency graph and shares that context with the Rule Engine. Circular and dead-object algorithms operate over the already resolved graph.

Repository Analysis JSON owns independent schema `1.0`. Existing Dependency, Impact, Circular, Dead Object and Static-analysis schemas are not silently extended.

The report preserves source/object provenance through the `SqlSource` + parsed-document pairing. No source field is added to `SqlDocument`, `SqlObject` or `Reference`.

The HTML report is self-contained and includes executive summary, source inventory, dependency overview, key objects, cycles, dead candidates, normalized findings, dynamic-SQL uncertainty, object explorer and source traceability. See `docs/unified-repository-analysis.md`.

## Source identity gate

Repository/file analysis must preserve physical identity until durable SQL ownership has been established. `SqlSource.source_id` is the canonical physical-source identifier and source-aware analysis uses `script:<source_id>` only for fallback Script scopes.

Durable schema objects keep their normal SQL identity. `SqlDocument`, `SqlObject`, `Reference` and existing serialized schemas do not gain source-path fields.

Raw-text `parse()` / `analyze_many()` methods remain compatibility surfaces. CLI file/directory analysis and source-aware analyzer APIs use `SqlSource`. See `docs/sql-source-identity.md`.

## Parser gates

The parser is dependency-oriented rather than a complete T-SQL compiler. Parser changes must be driven by reduced reproducible fixtures and preserve the public AST unless a separate versioned decision is made.

A physical `.sql` source may contain multiple durable objects. Each object owns only its own parameters, variables, references, temporary tables and dynamic-SQL evidence. Ownership closes on a new durable definition, a standalone `GO` batch boundary or end of document.

Procedure/function parameter parsing must distinguish optional outer signature parentheses from datatype parentheses. Datatype delimiters such as `nvarchar(320)`, `decimal(18,4)` and `datetime2(3)` must not terminate or split the logical parameter list. Assigning to an existing parameter with `SET` must not reclassify it as a local variable.

Inline foreign keys are structural dependencies: the defining table is the source and the referenced table is the target. `REFERENCES` is not treated as a generic relation keyword; `FOREIGN KEY` evidence is required in the same statement so permission syntax does not create false edges.

CTE aliases, temp tables and table variables must not become durable dependency nodes. `OPENJSON`, `OPENQUERY` and `OPENROWSET` are built-in/runtime rowset boundaries rather than local schema objects. Dynamic SQL remains uncertainty unless statically resolvable. The canonical graph direction remains `source -> target`.

Current syntax support is frozen in `docs/parser-support.md`; object ownership is frozen in `docs/object-scoped-parser.md`; physical source identity is frozen in `docs/sql-source-identity.md`. Real-repository evidence is recorded in the `docs/real-repository-validation*.md` series.

## Repository hygiene gate

`handoffs/` is the canonical handoff-note directory. The legacy singular `handoff/` path must not be recreated unless a separate migration decision explicitly supersedes this contract.

The `new-handoff` command remains compatible and writes to `handoffs/`.

## Static-analysis gates

All graph analyzers and rules reuse the canonical `source -> target` direction.

Circular Dependency Detection uses one strongly connected component as one circularity finding. Rule `SQL001` adapts this contract with severity `error`.

Dead Object Detection treats a component with no incoming static references from outside the component as a **candidate only**. Rule `SQL002` adapts this contract with severity `warning`; it preserves entry-point, trigger and external-usage safeguards. Script nodes are not dead-object candidates.

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
