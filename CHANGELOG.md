# Changelog

## 0.25.0 - 2026-08-08

### Added
- `RepositoryAnalysisResult` as the canonical product-level result for one complete SQL repository analysis.
- `RepositoryAnalysisEngine` that parses each `SqlSource` once, resolves one dependency graph and reuses that shared context for rules, cycles, dead-object candidates and repository inventory.
- Repository Analysis JSON schema `1.0` with summary metrics, source/object provenance, graph nodes/edges, cycles, dead-object candidates/exclusions, normalized findings and dynamic-SQL uncertainty.
- `RepositoryAnalysisReportGenerator` and exporter for a self-contained HTML report with executive metrics, inventory, dependency overview, key-object ranking, cycles, dead candidates, findings, uncertainty, searchable object explorer and source traceability.
- `sqlstudio repository-analysis` CLI command with recursive input, JSON output, HTML output, compact JSON and repeatable entry-point support.
- Public repository-analysis API exports and repository-checkout wrapper compatibility.
- Architecture contract in `docs/unified-repository-analysis.md` plus CLI/unit coverage.

### Changed
- Repository-level reporting now composes existing stable analyzers around one shared parse/graph context instead of requiring consumers to invoke separate commands and reconcile results.
- Key-object ranking uses incoming direct dependents from the canonical `source -> target` graph and remains informational rather than a new severity/rule.
- Source-to-object provenance is maintained by pairing `SqlSource` with its parsed document; the SQL AST itself remains unchanged.

### Safety and compatibility
- Existing Dependency, Cross Reference, Impact, Circular Dependency, Dead Object and Static-analysis JSON schemas are unchanged.
- `SqlDocument`, `SqlObject`, `Reference` and existing analyzer methods are unchanged.
- Dead Object findings remain review candidates only and serialize `safe_to_delete=false` in the unified report.
- Dynamic SQL remains an uncertainty boundary; the unified report does not invent dependencies that static analysis cannot prove.
- Dependency direction remains `source -> target`.
- PyPI publication remains out of scope.

## 0.24.0 - 2026-08-08

### Added
- `SqlSource` as the physical SQL input model with stable caller-controlled `source_id`, SQL text and optional path metadata.
- Source-aware `SQLParser.parse_source()` while retaining the historical text-only `parse()` API.
- `analyze_source()` / `analyze_sources()` entry points across Dependency, Cross Reference, Impact, Circular Dependency, Dead Object and Static-analysis analyzers.
- Regression fixtures and tests proving independent physical scripts remain distinct graph nodes.
- `docs/sql-source-identity.md` as the frozen architecture contract for physical-source provenance.
- CI smoke coverage for source identity through both the repository wrapper and the installed wheel outside the checkout.

### Fixed
- Multiple SQL files without durable schema definitions no longer collapse into the shared `UnnamedScript` node when analyzed through the repository/file pipeline.
- Script-level dependencies are now attributed to `script:<source_id>` rather than being merged across unrelated physical files.

### Changed
- CLI file and directory analysis preserves physical source identity until SQL object ownership is established.
- CLI source IDs are repository-relative to the current working directory when possible and otherwise use normalized absolute paths.
- `SqlSource.source_id` normalizes path separators to `/` and removes leading `./`.

### Compatibility
- Public `SqlDocument`, `SqlObject`, `Reference` and existing serialized schemas remain unchanged.
- Durable SQL objects keep their schema identity; only fallback Script scopes receive `script:<source_id>` names.
- Raw-text `parse()`, `analyze()` and `analyze_many()` methods remain supported with historical behavior, including `UnnamedScript` where applicable.
- The repository compatibility wrapper retains its historical text-reader helper.
- Canonical dependency direction remains `source -> target`.

## 0.23.0 - 2026-08-08

### Added
- Real-repository procedure-signature regression coverage derived from PULSE export procedures.
- Parameterized datatype coverage for `nvarchar(...)`, `decimal(...,...)` and `datetime2(...)` in both procedure and function signatures.
- Case-insensitive regression coverage proving `SET @Parameter = ...` does not duplicate a parameter as a local variable.
- `docs/real-repository-validation-pass-3.md` documenting the parameter-list boundary and variable-classification defects.

### Fixed
- Datatype closing parentheses no longer terminate an unparenthesized stored-procedure parameter list.
- Commas inside datatype precision/scale syntax such as `decimal(18,4)` no longer split logical parameters.
- Parenthesized function signatures with parameterized datatypes retain all parameters.
- Procedure input-normalization assignments no longer pollute `SqlObject.variables` when the target is already a parameter.

### Changed
- Parameter parsing now tracks datatype nesting independently from the optional outer signature parentheses.
- Parameter/local-variable separation is case-insensitive within the owning object scope.

### Compatibility
- Public `Parameter`, `Variable`, `SqlObject` and `SqlDocument` fields remain unchanged.
- Parameter datatype metadata continues to expose the logical datatype identifier; this milestone fixes boundaries rather than changing the AST schema.
- Dependency graph and downstream analysis semantics are unchanged.

## 0.22.0 - 2026-08-08

### Added
- Inline foreign-key dependency extraction for `FOREIGN KEY (...) REFERENCES schema.Table (...)` constraints.
- Reduced real-repository regression fixture derived from the PULSE import-foundation schema shape.
- Explicit regression coverage proving child-table dependency edges use the object-scoped durable table as their source.
- Negative coverage for `GRANT REFERENCES ON ...` permission syntax so `REFERENCES` is not treated as a generic relation keyword.
- `docs/real-repository-validation-pass-2.md` documenting the evidence, fix and deferred standalone `ALTER TABLE` ownership boundary.

### Fixed
- Dependency graphs no longer omit inline foreign-key relationships between locally defined tables.
- `REFERENCES` permission syntax does not create a false dependency target named `ON`.

### Changed
- Parser support now distinguishes DDL foreign-key evidence from permission syntax using same-statement `FOREIGN KEY` evidence.
- Real-repository dogfooding continues to drive parser coverage after the `0.21.0` object-scoped architecture milestone.

### Compatibility
- Public AST fields and serialized schemas remain unchanged.
- Dependency direction remains `source -> target`.
- Standalone `ALTER TABLE ... FOREIGN KEY` source ownership is deliberately not approximated as a Script-sourced schema edge.

## 0.21.0 - 2026-08-08

### Added
- Object-scoped parser ownership for multiple durable SQL definitions in one physical `.sql` source.
- Standalone `GO` batch-boundary detection that closes the active object scope without treating identifiers named `GO` as separators.
- Guarded durable DDL discovery for migration patterns such as `IF OBJECT_ID(...) ... CREATE TABLE ...`.
- Stored-procedure parameter extraction for both parenthesized and conventional unparenthesized T-SQL syntax.
- `tests/fixtures/object_scopes/` plus regression tests proving isolation of parameters, variables, references, temporary tables and dynamic-SQL evidence.
- `docs/object-scoped-parser.md` as the architecture contract for parser evidence ownership.
- CI smoke coverage for object-scoped parsing through both the repository wrapper and the installed wheel.

### Changed
- `ParserContext` now materializes immutable `SqlObject` instances at object, batch and document boundaries instead of accumulating all evidence globally for the first object.
- Creation parsing can locate supported durable definitions inside guarded statements instead of requiring `CREATE` to be the first token.
- Variable declaration discovery now works when the first `DECLARE` appears in the same semicolon-delimited statement as a module header.
- Parser support and architecture documentation now guarantee multi-definition sources when ownership boundaries can be established.

### Fixed
- References, parameters, variables, temporary tables and dynamic-SQL flags no longer leak from one durable object to another object defined later in the same source file.
- Dependency graphs now use the correct object as the source for edges produced from multi-definition files.

### Compatibility
- Public `SqlDocument`, `SqlObject` and `Reference` fields remain unchanged.
- Dependency direction remains `source -> target`.
- Dependency Resolver, Cross Reference, Impact Analysis, Circular Dependency, Dead Object and Rule Engine public semantics remain unchanged.
- Existing one-object-per-file repositories remain supported.

## 0.20.0 - 2026-08-08

### Added
- First documented real-repository dogfooding pass with reduced, synthetic regression fixtures derived from observed SQL shapes.
- `tests/fixtures/real_repository/` coverage for JSON staging and temp-only utility scripts.
- `docs/real-repository-validation.md` with evidence, corrected defects, continuing validation rules and the explicit multi-definition architecture boundary.

### Fixed
- `OPENJSON(...)` is no longer emitted as a false durable schema dependency when used after `FROM` or `JOIN`.
- `CREATE TABLE #temp` and `CREATE TABLE ##temp` no longer register transient tables as durable `Table` objects.
- Utility scripts whose first created relation is temporary now retain the existing `Script` fallback instead of contaminating the dependency graph with a temporary-table source object.

### Changed
- Parser support documentation now treats built-in rowset suppression as evidence-driven and includes `OPENJSON` alongside `OPENQUERY` and `OPENROWSET`.
- Real-repository validation becomes the default source of parser-hardening work.
- Multiple independent durable `CREATE` definitions in one source file are elevated from a generic limitation to an explicit architecture decision; no silent approximation is introduced.

### Compatibility
- Public AST models, graph direction, CLI commands and serialized analysis schemas remain unchanged.
- Dynamic SQL remains an uncertainty boundary.

## 0.19.0 - 2026-08-08

### Added
- Formal handoff-layout contract declaring `handoffs/` as the single canonical repository path.
- Regression coverage proving `new-handoff` creates documents under the plural canonical directory and the singular legacy path is absent.
- Expanded human-readable handoff template with current-state, validation, decision/risk and next-action sections.
- Controlled GitHub Release workflow triggered only after successful `CI` completion on `main`.
- GitHub-only release policy with immutable stable SemVer tags and wheel/sdist release assets.
- Release-policy regression tests and an explicit `main` branch-protection target configuration.

### Removed
- Legacy `handoff/handoff.schema.json`, an unused 44-byte stub with no properties, version, package consumer, tests or CLI integration.
- Duplicate singular `handoff/` repository path.

### Changed
- Roadmap and historical audit remediation status now mark handoff-directory drift as resolved.
- Release/tag policy is resolved as GitHub Releases only; PyPI publication remains explicitly deferred.
- Branch protection becomes the remaining repository-administration gate after the first controlled release.

### Compatibility
- `sqlstudio new-handoff <name>` remains supported and continues writing to `handoffs/<name>.md`.
- No package API, CLI command or analysis schema changes are introduced by release automation.

## 0.18.0 - 2026-08-08

### Added
- Representative complex T-SQL regression corpus covering bracketed/multipart names, CTEs, multiple joins, derived tables, `MERGE`, alias-targeted `UPDATE` and transient temp-table behavior.
- Shared multipart-name normalization for parser creation, execution and relation-reference paths.
- Formal `docs/parser-support.md` contract documenting supported dependency-oriented syntax and known parser boundaries.

### Fixed
- Relation parsing now collects all resolvable references in one statement instead of stopping after the first relation keyword.
- Bracket-quoted multipart identifiers are tokenized as one logical identifier and normalized into database/schema/name fields.
- CTE aliases, temp tables and table variables no longer become durable dependency targets in the hardened relation scanner.
- `MERGE ... WHEN MATCHED THEN UPDATE SET` no longer emits a false dependency named `SET`.
- `UPDATE alias ... FROM schema.Table AS alias` resolves the alias to the real table when statement-local evidence exists.
- SQL string tokenization now respects doubled quote escaping.
- Duplicate references within one parsed source object are suppressed case-insensitively.

### Changed
- Parser scope is explicitly dependency-oriented, not a claim of full T-SQL grammar support.
- Roadmap advances to `handoff/` versus `handoffs/` repository hygiene.

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
- Aligned README, architecture, CLI documentation, roadmap and project version with the implemented baseline.
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
