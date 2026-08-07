# Changelog

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
