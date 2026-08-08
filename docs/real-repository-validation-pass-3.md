# Real Repository Validation — Pass 3

## Scope

This pass validates procedure-signature parsing against the PULSE export implementation, especially:

`rubensv74/app_pulse/sql/export/002_register_punch_export_snapshot.sql`

The production source uses conventional SQL Server procedure signatures without an outer parenthesized parameter list and includes parameterized datatypes such as `nvarchar(30)`, `nvarchar(320)` and `datetime2(3)`.

## Observed defects

### Datatype closing parentheses terminated the parameter list

The earlier parser treated any `)` encountered while reading parameters as the end of the module parameter list. In an unparenthesized stored-procedure signature this meant a datatype such as:

```sql
@ExportType nvarchar(30),
@CreatedBy nvarchar(320),
@ExpiresAtUtc datetime2(3) = NULL
```

could stop parsing at the first datatype closing parenthesis and omit later parameters.

The same ambiguity could affect parenthesized function signatures containing datatypes such as `decimal(18,4)`.

### Parameter normalization polluted local variables

PULSE procedures normalize inputs with statements such as:

```sql
SET @ExportType = NULLIF(LTRIM(RTRIM(@ExportType)), N'');
```

The declaration scanner previously treated `SET @name` as variable evidence even when `@name` was already a procedure parameter. This could duplicate parameters in `SqlObject.variables`.

## Resolution in 0.23.0

Parameter parsing now tracks nested datatype parentheses separately from the optional outer parameter-list parentheses.

- commas inside `decimal(18,4)` do not split parameters;
- `)` inside `nvarchar(30)` or `datetime2(3)` does not end the whole list;
- parenthesized function parameter lists still close at their outer `)`;
- unparenthesized procedure lists stop at module-boundary keywords such as `AS`;
- defaults and `OUTPUT` flags continue to be captured;
- `ParserContext.add_variable()` ignores names already registered as parameters, case-insensitively.

## Reduced regression fixture

`tests/fixtures/object_scopes/procedure_parameters.sql` models the observed shape with synthetic values and verifies:

- all seven parameters survive multiple parameterized datatypes;
- `decimal(18,4)` does not split at its inner comma;
- `datetime2(3) = NULL` retains its default;
- `OUTPUT` remains attached to the correct parameter;
- input-normalization `SET` statements do not duplicate parameters as local variables;
- real `DECLARE` variables remain visible;
- parenthesized function signatures with parameterized datatypes remain supported.

## Compatibility

This pass changes no public AST fields and no graph semantics. It improves the accuracy of existing `Parameter` and `Variable` collections inside the already-approved object-scoped ownership model.
