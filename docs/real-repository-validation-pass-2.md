# Real Repository Validation — Pass 2

## Scope

This pass validates the `0.21.0` object-scoped parser against a real multi-definition migration/foundation script from the PULSE repository:

`rubensv74/app_pulse/sql/import/001_import_foundations.sql`

The source was inspected as repository evidence. SQL Studio regression fixtures use reduced synthetic structures and do not copy application data.

## Observed structure

The script contains several guarded durable table definitions in one physical file and uses inline foreign-key constraints such as:

```sql
CONSTRAINT [FK_ExportBatchRow_ExportBatch]
    FOREIGN KEY ([ExportBatchId])
    REFERENCES [warroom].[ExportBatch] ([ExportBatchId])
```

The `0.21.0` object-scoped architecture correctly provides a durable owner for each `CREATE TABLE`, but the relation parser did not previously promote `REFERENCES` targets into dependency edges.

## Correctness defect

Without foreign-key evidence, a graph could show both tables as local definitions while omitting the structural dependency:

```text
warroom.ExportBatchRow -> warroom.ExportBatch
```

That omission propagates into Cross Reference, Impact Analysis, Circular Dependency and Dead Object reasoning.

## Resolution in 0.22.0

SQL Studio now records the target of an inline `FOREIGN KEY ... REFERENCES ...` constraint as a normal durable reference owned by the defining table.

The implementation deliberately does not add `REFERENCES` to the generic relation-keyword set. Permission syntax such as:

```sql
GRANT REFERENCES ON OBJECT::warroom.ExportBatch TO app_role;
```

must not create a false dependency named `ON`. A `REFERENCES` target is therefore collected only when a `FOREIGN KEY` clause exists earlier in the same statement.

## Reduced regression fixture

`tests/fixtures/object_scopes/foreign_key_foundations.sql` represents the observed shape with synthetic table and role names. Regression tests prove:

- guarded tables remain separate durable objects;
- each child table owns its foreign-key reference;
- the dependency graph contains child-to-parent edges;
- permission-only `GRANT REFERENCES` does not create a Script object or schema dependency;
- canonical graph direction remains `source -> target`.

## Deferred boundary

Standalone `ALTER TABLE ... ADD CONSTRAINT ... FOREIGN KEY ... REFERENCES ...` is a separate ownership case. A target can be detected syntactically, but a correct graph also requires the altered durable table to be established as the source object.

SQL Studio does not emit a misleading `Script -> referenced_table` edge as a shortcut. This boundary will be revisited only when representative repository evidence requires it.

## Outcome

This pass increases graph fidelity without changing the public AST, object-scope architecture, dependency direction or downstream analysis schemas.
