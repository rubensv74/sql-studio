# Representative T-SQL parser corpus

These fixtures exercise dependency-relevant syntax rather than attempting exhaustive T-SQL grammar coverage.

- `complex_view.sql`: `CREATE OR ALTER`, bracketed names, three-part cross-database name, CTE suppression, multiple joins and a derived table.
- `merge_update.sql`: `MERGE INTO ... USING` plus `UPDATE alias ... FROM` resolution.
- `temp_and_derived.sql`: `SELECT INTO #temp`, derived query and suppression of transient temp dependencies.

Expected behavior is asserted in `tests/test_tsql_complex_parser.py`. Add a reduced reproducible fixture when a new parser defect affects dependency evidence.
