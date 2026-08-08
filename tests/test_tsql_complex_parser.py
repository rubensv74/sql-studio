from __future__ import annotations

import unittest
from pathlib import Path

from sqlstudio import SQLParser
from sqlstudio.parser.tokenizer import SQLTokenizer


FIXTURES = Path(__file__).resolve().parent / "fixtures" / "tsql_complex"


def reference_keys(sql_text: str) -> set[tuple[str | None, str | None, str]]:
    document = SQLParser().parse(sql_text)
    return {
        (reference.database, reference.schema, reference.name)
        for reference in document.objects[0].references
        if reference.kind == "reference"
    }


class ComplexTsqlParserTests(unittest.TestCase):
    def test_tokenizer_keeps_bracketed_multipart_identifier_together(self) -> None:
        tokens = SQLTokenizer("SELECT * FROM [OtherDb].[sales].[Order Header]").tokenize()
        identifiers = [token.value for token in tokens if token.kind == "identifier"]
        self.assertIn("[OtherDb].[sales].[Order Header]", identifiers)

    def test_tokenizer_handles_escaped_string_quotes(self) -> None:
        tokens = SQLTokenizer("SELECT 'O''Brien' AS Name").tokenize()
        literals = [token.value for token in tokens if token.kind == "literal"]
        self.assertEqual(literals, ["'O''Brien'"])

    def test_complex_view_collects_all_real_relations_and_suppresses_cte(self) -> None:
        sql = (FIXTURES / "complex_view.sql").read_text(encoding="utf-8")
        document = SQLParser().parse(sql)
        obj = document.objects[0]
        self.assertEqual((obj.schema, obj.name, obj.object_type), ("reporting", "Order Summary", "View"))
        self.assertEqual(
            reference_keys(sql),
            {
                ("OtherDb", "sales", "Order Header"),
                (None, "crm", "Customer Master"),
                (None, "audit", "Order Flags"),
            },
        )

    def test_merge_and_update_alias_resolve_to_real_objects(self) -> None:
        sql = (FIXTURES / "merge_update.sql").read_text(encoding="utf-8")
        self.assertEqual(
            reference_keys(sql),
            {
                (None, "warehouse", "Order Fact"),
                (None, "staging", "Order Stage"),
                (None, "crm", "Customer Master"),
            },
        )

    def test_temp_and_derived_sources_do_not_create_durable_temp_dependency(self) -> None:
        sql = (FIXTURES / "temp_and_derived.sql").read_text(encoding="utf-8")
        document = SQLParser().parse(sql)
        obj = document.objects[0]
        self.assertIn("#Snapshot", obj.temporary_tables)
        self.assertEqual(
            reference_keys(sql),
            {
                (None, "dbo", "SourceRows"),
                (None, "dbo", "OtherRows"),
            },
        )

    def test_multiple_joins_in_one_statement_are_all_collected(self) -> None:
        sql = (
            "CREATE VIEW dbo.V AS SELECT a.Id FROM dbo.A a "
            "JOIN dbo.B b ON b.Id=a.Id LEFT JOIN dbo.C c ON c.Id=a.Id"
        )
        self.assertEqual(
            reference_keys(sql),
            {(None, "dbo", "A"), (None, "dbo", "B"), (None, "dbo", "C")},
        )


if __name__ == "__main__":
    unittest.main()
