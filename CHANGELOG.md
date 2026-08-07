# Changelog

## 0.17.0 - 2026-08-08

### Added
- Formal performance-tooling scope decision with explicit post-MVP re-entry gates for profiler and benchmark capabilities.
- Repository contract test ensuring unsupported profiler/benchmark stubs do not silently return to the stabilized baseline.

### Changed
- Architecture now treats runtime profiler/benchmark tooling as a separate future observability boundary rather than an unfinished MVP subsystem.
- Roadmap advances to representative complex T-SQL parser hardening.
- Historical audit remediation status is aligned with the packaging, license and performance-scope decisions completed after baseline stabilization.

### Removed
- Unsupported `cli/profiler.py` template generator that performed no profiling.
- Unsupported `cli/benchmark.py` recorder that stored caller-provided metrics without measuring them.
- Duplicate/incomplete profiler and benchmark schemas under `profiler/`, `benchmark/` and `core/`.
- Heading-only `benchmarks/BENCHMARK_TEMPLATE.md` artifact.

### Compatibility
- No public `sqlstudio` package API, installed console command or supported analysis schema was removed.

## 0.16.0 - 2026-08-08

### Added
- Standard Python packaging through `pyproject.toml` and setuptools PEP 517 backend.
- Buildable source distribution and platform-independent wheel for SQL Studio.
- Installed `sqlstudio` console entry point backed by `sqlstudio.cli:main`.
- Public `sqlstudio.__version__` and `sqlstudio --version` support.
- Packaging regression tests and CI gates that build and install the wheel before executing a real analysis outside the repository checkout.
- Workflow artifact upload for generated `dist/` packages.
- Complete MIT license text included in package metadata/distributions.

### Changed
- Canonical CLI implementation moved to `src/sqlstudio/cli.py`.
- `cli/sqlstudio.py` is now a backward-compatible wrapper that reexports the canonical callable surface.
- `core/version.txt` is retained as a compatibility mirror of the canonical package version.
- README, CLI, architecture and roadmap now treat the installed `sqlstudio` command as the primary invocation.
- Roadmap advances to profiler/benchmark scope reassessment.

### Fixed
- Repository-wrapper module compatibility is preserved for tests and consumers that import CLI helper functions directly.

## 0.15.0 - 2026-08-08

### Added
- Consolidated `StaticAnalysisRuleEngine` with a shared `RuleContext`, normalized `Finding`/`RuleResult` models and stable severity levels (`info`, `warning`, `error`).
- `StaticAnalysisAnalyzer` that parses each SQL input once and builds one dependency graph for all selected rules.
- Built-in `SQL001` Circular Dependency rule with default severity `error`.
- Built-in `SQL002` Dead Object Candidate rule with default severity `warning` while preserving the candidate-only safety contract.
- Deterministic consolidated JSON schema `1.0` with rule, finding, severity and shared graph/parser summaries.
- New `analyze` CLI command with repeatable `--rule` and `--entry-point` options.
- Optional `--fail-on info|warning|error` quality gate using exit code `2` while retaining JSON diagnostics.
- Rule-engine API, analyzer, serialization and CLI regression coverage plus CI smoke gates.

### Changed
- Public package exports now expose Rule Engine models, built-in rules, analyzer, engine and serializer.
- Architecture explicitly distinguishes structural analysis services from actionable static-analysis rules.
- Existing Circular Dependency and Dead Object APIs/CLI contracts remain supported as compatibility surfaces.
- Roadmap advances to Packaging and installable CLI.

## 0.14.0 - 2026-08-08

### Added
- Conservative Dead Object Detection for locally defined root components without incoming static references.
- SCC-aware grouping so isolated circular islands are returned as one dead-object candidate finding.
- Repeatable `--entry-point` exclusions for known externally invoked SQL objects.
- Automatic trigger-root exclusion for implicit database invocation.
- Dead Object JSON schema `1.0` with explicit uncertainty and `safe_to_delete=false` contract.
- Dynamic SQL object count and uncertainty flag.
- `dead-objects` CLI command, regression tests, reproducible fixture and CI smoke validation.

### Fixed
- Dependency resolution now registers definitions before references so local object metadata is not left as `Unknown` when file order changes.
- `EXEC sp_executesql ...` is now marked as dynamic SQL.

### Changed
- Public package exports, architecture, CLI documentation and roadmap include Dead Object Detection.
- Roadmap advances to Static-analysis Rule Engine Consolidation.

## 0.13.0 - 2026-08-08

### Added
- Circular Dependency Detection based on strongly connected components.
- Self-reference detection for single-object cycles.
- Deterministic JSON schema `1.0` with cycle/object summaries, members and internal edges.
- Public Circular Dependency API and `circular-dependencies` CLI command.
- Unit, analyzer, serializer and CLI regression coverage for circular dependencies.
- CI smoke validation for the new command.

### Changed
- Roadmap advanced to Dead Object Detection.
- Architecture and CLI documentation formalized SCCs as the unit of circular-dependency reporting.

## 0.12.0 - 2026-08-08

### Added
- Transitive Impact Analysis to the stabilized product baseline.
- Self-contained HTML impact reports with hierarchical impact tree.
- GitHub Actions validation on Python 3.12.

### Fixed
- Impact Analysis now traverses incoming dependents instead of outgoing dependencies.
- HTML reports now derive direct and indirect impact from the analysis tree.
- HTML export now creates missing parent directories.
- Impact report contract test now verifies the documentation file and required sections.

### Changed
- Formalized `source -> target` dependency semantics in architecture documentation.
- Confirmed Impact JSON schema `1.0` remains flat; tree serialization is deferred to a future schema version.
- Aligned README, CLI documentation, roadmap and project version with the implemented baseline.
- Standardized documented runtime support on Python 3.12+.

### Removed
- Versioned Python bytecode and `__pycache__` directories.
- Unused legacy dependency model in `core/dependency_models.py`.
- Stale `core/sqlstudio.json` metadata that duplicated and contradicted the canonical version.

## 0.11.0

### Added
- Cross Reference Engine
- CrossReference models
- CrossReferenceAnalyzer
- CrossReference serialization
- CLI cross-references
- Architecture documentation
