from __future__ import annotations

import unittest
from pathlib import Path

from sqlstudio import SQLParser


FIXTURES = Path(__file__).resolve().parent / "fixtures" / "real_repository"


def reference_keys(sql_text: str) -> set[tuple[str | None, str | None, str]]:
    document = SQLParser().parse(sql_text)
    if not document.objects:
        return set()
    return {
        (reference.database, reference.schema, reference.name)
        for reference in document.objects[0].references
        if reference.kind == "reference"
    }


class RealRepositoryParserTests(unittest.TestCase):
    def test_openjson_is_not_emitted_as_schema_dependency(self) -> None:
        sql = (FIXTURES / "json_stage_procedure.sql").read_text(encoding="utf-8")
        document = SQLParser().parse(sql)
        obj = document.objects[0]

        self.assertEqual((obj.schema, obj.name, obj.object_type), ("ops", "usp_LoadPayload", "Stored Procedure"))
        self.assertIn("#Stage", obj.temporary_tables)
        self.assertEqual(reference_keys(sql), {(None, "dbo", "ReferenceData")})

    def test_temp_only_utility_script_remains_script_not_table(self) -> None:
        sql = (FIXTURES / "utility_catalog_script.sql").read_text(encoding="utf-8")
        document = SQLParser().parse(sql)
        obj = document.objects[0]

        self.assertEqual((obj.schema, obj.name, obj.object_type), (None, "UnnamedScript", "Script"))
        self.assertIn("#ObjectDefinitions", obj.temporary_tables)
        self.assertEqual(
            reference_keys(sql),
            {
                (None, "sys", "tables"),
                (None, "sys", "schemas"),
            },
        )

    def test_update_alias_of_temp_table_is_not_a_durable_dependency(self) -> None:
        sql = (FIXTURES / "update_temp_alias.sql").read_text(encoding="utf-8")
        document = SQLParser().parse(sql)
        obj = document.objects[0]
        references = {
            (reference.database, reference.schema, reference.name)
            for reference in obj.references
            if reference.kind == "reference"
        }

        self.assertEqual((obj.schema, obj.name), ("warroom", "usp_UpdateSnapshot"))
        self.assertIn("#ExportBase", obj.temporary_tables)
        self.assertEqual(references, {(None, "dbo", "SourceRows")})
        self.assertNotIn((None, None, "eb"), references)


if __name__ == "__main__":
    unittest.main()
