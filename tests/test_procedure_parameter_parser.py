from __future__ import annotations

import unittest
from pathlib import Path

from sqlstudio import SQLParser


FIXTURE = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "object_scopes"
    / "procedure_parameters.sql"
)


class ProcedureParameterParserTests(unittest.TestCase):
    def test_unparenthesized_procedure_parameters_survive_type_parentheses(self) -> None:
        document = SQLParser().parse(FIXTURE.read_text(encoding="utf-8"))
        procedure = document.objects[0]

        self.assertEqual(procedure.name, "usp_RegisterSnapshot")
        self.assertEqual(
            [parameter.name for parameter in procedure.parameters],
            [
                "@LogId",
                "@ProjectId",
                "@ExportType",
                "@CreatedBy",
                "@Amount",
                "@ExpiresAtUtc",
                "@IsReady",
            ],
        )
        self.assertEqual(
            [parameter.datatype for parameter in procedure.parameters],
            ["bigint", "bigint", "nvarchar", "nvarchar", "decimal", "datetime2", "bit"],
        )

        by_name = {parameter.name: parameter for parameter in procedure.parameters}
        self.assertEqual(by_name["@Amount"].default_value, "0")
        self.assertEqual(by_name["@ExpiresAtUtc"].default_value, "NULL")
        self.assertEqual(by_name["@IsReady"].default_value, "0")
        self.assertTrue(by_name["@IsReady"].output)

    def test_parameter_normalization_set_does_not_duplicate_local_variables(self) -> None:
        document = SQLParser().parse(FIXTURE.read_text(encoding="utf-8"))
        procedure = document.objects[0]

        self.assertEqual(
            [variable.name for variable in procedure.variables],
            ["@LocalBatchId", "@LocalStatus"],
        )

    def test_parameter_variable_deduplication_is_case_insensitive(self) -> None:
        document = SQLParser().parse(
            "CREATE PROCEDURE dbo.P @Value int AS BEGIN SET @VALUE = 1; END;"
        )
        procedure = document.objects[0]

        self.assertEqual([parameter.name for parameter in procedure.parameters], ["@Value"])
        self.assertEqual(procedure.variables, [])

    def test_parenthesized_function_parameters_allow_parameterized_datatypes(self) -> None:
        document = SQLParser().parse(
            "CREATE FUNCTION dbo.F(@Amount decimal(18,4), @Label nvarchar(50)) "
            "RETURNS int AS BEGIN RETURN 1 END;"
        )
        function = document.objects[0]

        self.assertEqual(
            [parameter.name for parameter in function.parameters],
            ["@Amount", "@Label"],
        )
        self.assertEqual(
            [parameter.datatype for parameter in function.parameters],
            ["decimal", "nvarchar"],
        )


if __name__ == "__main__":
    unittest.main()
