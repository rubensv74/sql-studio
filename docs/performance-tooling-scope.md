# Performance Tooling Scope Decision

## Status

**Decision:** runtime profiler and benchmark tooling are **deferred to post-MVP** and are not part of SQL Studio's stabilized static-analysis product baseline.

This is a scope decision, not an assertion that performance tooling has no future value.

## Audit evidence

The pre-decision repository contained several artifacts that looked like implemented capabilities but did not meet SQL Studio's product gates:

| Artifact | Observed behavior | Decision |
| --- | --- | --- |
| `cli/profiler.py` | Writes an empty JSON template; performs no profiling or measurement. | Remove unsupported stub. |
| `profiler/profile.schema.json` | Minimal unconstrained shape with `timeline` and `summary`; no producer/consumer contract. | Remove unsupported schema. |
| `cli/benchmark.py` | Persists caller-supplied elapsed/CPU/read values; it does not execute or measure a benchmark. | Remove unsupported stub. |
| `benchmark/benchmark.schema.json` | Requires only `project` and `elapsed_ms`; no implementation validates against it. | Remove duplicate unsupported schema. |
| `core/benchmark.schema.json` | Separate incompatible benchmark schema containing only title/type. | Remove duplicate unsupported schema. |
| `benchmarks/BENCHMARK_TEMPLATE.md` | Heading-only result template; no executable benchmark corpus or protocol. | Remove unsupported template. |

No profiler/benchmark artifact was exposed by the installable `sqlstudio` package, covered by automated tests, exercised by GitHub Actions, or documented as a supported CLI command.

## Why this is outside the MVP

SQL Studio's current architecture performs repository-only static analysis without requiring a live database connection. A meaningful runtime profiler would cross that boundary and introduce additional concerns:

- database connectivity and credentials;
- target-server compatibility and permissions;
- runtime workload capture and privacy;
- measurement overhead and observer effects;
- normalization across SQL Server versions and hardware;
- safe collection of execution plans, CPU, duration and logical reads.

A meaningful benchmark facility has different requirements again:

- a reproducible SQL/project corpus;
- controlled warm/cold-cache semantics;
- repeat counts and variance reporting;
- environment metadata;
- comparable baselines and regression thresholds;
- protection against noisy CI measurements.

Implementing either now would expand the product from static repository analysis into runtime database observability before the static-analysis MVP has finished hardening.

## Re-entry gate

Performance tooling may return to the roadmap only when a concrete product requirement exists. A future proposal must define, before implementation:

1. **Question answered** — what user decision the profiler or benchmark enables.
2. **Execution boundary** — repository-only, local SQL Server, remote SQL Server, or imported telemetry.
3. **Metric provenance** — metrics must be measured or imported from an explicit source, never merely accepted as if SQL Studio measured them.
4. **Schema contract** — versioned and validated output with units and nullable/required semantics.
5. **Safety boundary** — credential handling, sensitive SQL text and telemetry retention rules.
6. **Reproducibility** — repeat strategy, environment metadata and variance treatment.
7. **Package/API design** — implementation under `src/sqlstudio/`, not standalone orphan scripts.
8. **Tests and CI** — deterministic unit/contract coverage; performance thresholds must not create flaky generic CI gates.
9. **Documentation** — supported workflows, limitations and interpretation guidance.

Until those gates are met, `profiler`, `benchmark` and `benchmarks` are reserved concepts rather than implemented SQL Studio capabilities.

## Compatibility

The removed artifacts were unsupported repository stubs. No public `sqlstudio` package API, installed console command, JSON analysis schema, or documented supported command is removed by this decision.
