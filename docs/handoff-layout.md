# Handoff Repository Layout

## Decision

`handoffs/` is the single canonical repository directory for SQL Studio handoff documents.

The legacy singular directory `handoff/` is retired.

## Evidence

Before consolidation:

- `src/sqlstudio/cli.py::create_handoff()` already wrote new documents to `handoffs/<name>.md`;
- `handoffs/` contained the human-readable handoff template;
- `handoff/` contained only a 44-byte `handoff.schema.json` declaring an object title/type;
- the singular schema had no package consumer, CLI integration, automated test or documented supported workflow.

The duplicate singular path therefore represented repository drift rather than a second supported contract.

## Compatibility

The `new-handoff` CLI command remains available and continues writing to:

```text
handoffs/<name>.md
```

No installed command or public package API is removed by this cleanup.

The retired `handoff/handoff.schema.json` is not migrated because it was not a functional schema contract: it contained no properties, required fields, version or validation integration.

## Template

`handoffs/HANDOFF_TEMPLATE.md` is the canonical human-readable structure for manually maintained handoff notes. It records:

- current state;
- completed changes;
- validation evidence;
- open decisions/risks;
- next actions.

The CLI-generated handoff remains intentionally minimal for backward compatibility; consumers may expand it using the canonical template.

## Repository gate

Future changes must not recreate both `handoff/` and `handoffs/`. If a machine-readable handoff schema is needed later, it must be versioned and placed under the canonical `handoffs/` area or an explicitly approved package schema location.
