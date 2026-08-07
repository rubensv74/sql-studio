# Changelog

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
