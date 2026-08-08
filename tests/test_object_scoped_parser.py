from __future__ import annotations

import unittest
from pathlib import Path

from sqlstudio import DependencyAnalyzer, SQLParser


FIXTURES = Path(__file__).resolve().parent / "fixtures" / "object_scopes"


def object_by_name(sql_text: str, name: str):
    document = SQLParser().parse(sql_text)
    return next(obj for obj in document.objects if obj.name == name)


def reference_names(obj) -> set[str]:
    return {reference.name for reference in obj.references}


class ObjectScopedParserTests(unittest.TestCase):
    def test_multiple_modules_keep_evidence_in_their_own_scope(self) -> None:
        sql = (FIXTURES / "multi_modules.sql").read_text(encoding="utf-8")
        document = SQLParser().parse(sql)

        self.assertEqual(
            [(obj.schema, obj.name, obj.object_type) for obj in document.objects],
            [
                ("dbo", "ProcA", "Stored Procedure"),
                ("dbo", "ProcB", "Stored Procedure"),
            ],
        )

        proc_a = object_by_name(sql, "ProcA")
        proc_b = object_by_name(sql, "ProcB")

        self.assertEqual([parameter.name for parameter in proc_a.parameters], ["@Id"])
        self.assertEqual([parameter.name for parameter in proc_b.parameters], ["@Code"])
        self.assertEqual([variable.name for variable in proc_a.variables], ["@LocalA"])
        self.assertEqual([variable.name for variable in proc_b.variables], ["@LocalB"])

        self.assertIn("SourceA", reference_names(proc_a))
        self.assertIn("sp_executesql", reference_names(proc_a))
        self.assertNotIn("SourceB", reference_names(proc_a))
        self.assertNotIn("HelperB", reference_names(proc_a))

        self.assertIn("SourceB", reference_names(proc_b))
        self.assertIn("HelperB", reference_names(proc_b))
        self.assertNotIn("SourceA", reference_names(proc_b))
        self.assertNotIn("sp_executesql", reference_names(proc_b))

        self.assertTrue(proc_a.dynamic_sql)
        self.assertFalse(proc_b.dynamic_sql)
        self.assertIn("#StageA", proc_a.temporary_tables)
        self.assertNotIn("#StageA", proc_b.temporary_tables)

    def test_guarded_migration_batches_expose_each_durable_table(self) -> None:
        sql = (FIXTURES / "guarded_tables.sql").read_text(encoding="utf-8")
        document = SQLParser().parse(sql)

        self.assertEqual(
            [(obj.schema, obj.name, obj.object_type) for obj in document.objects],
            [
                ("warroom", "ExportBatch", "Table"),
                ("warroom", "ImportBatch", "Table"),
            ],
        )

    def test_dependency_graph_uses_each_object_as_its_own_source(self) -> None:
        sql = (FIXTURES / "multi_modules.sql").read_text(encoding="utf-8")
        graph = DependencyAnalyzer().analyze(sql)

        proc_a_dependencies = {node.name for node in graph.dependencies_of("dbo.ProcA")}
        proc_b_dependencies = {node.name for node in graph.dependencies_of("dbo.ProcB")}

        self.assertIn("dbo.SourceA", proc_a_dependencies)
        self.assertNotIn("dbo.SourceB", proc_a_dependencies)
        self.assertIn("dbo.SourceB", proc_b_dependencies)
        self.assertNotIn("dbo.SourceA", proc_b_dependencies)

    def test_inline_foreign_keys_create_edges_from_owning_tables(self) -> None:
        sql = (FIXTURES / "foreign_key_foundations.sql").read_text(encoding="utf-8")
        document = SQLParser().parse(sql)

        export_row = object_by_name(sql, "ExportBatchRow")
        import_batch = object_by_name(sql, "ImportBatch")
        self.assertEqual(reference_names(export_row), {"ExportBatch"})
        self.assertEqual(reference_names(import_batch), {"ExportBatch"})

        graph = DependencyAnalyzer().analyze(sql)
        self.assertEqual(
            {node.name for node in graph.dependencies_of("warroom.ExportBatchRow")},
            {"warroom.ExportBatch"},
        )
        self.assertEqual(
            {node.name for node in graph.dependencies_of("warroom.ImportBatch")},
            {"warroom.ExportBatch"},
        )

        # The final GRANT REFERENCES batch is permission-only. It must not
        # create a synthetic Script object or a dependency target named ON.
        self.assertFalse(any(obj.object_type == "Script" for obj in document.objects))

    def test_grant_references_permission_is_not_foreign_key_dependency(self) -> None:
        document = SQLParser().parse(
            "GRANT REFERENCES ON OBJECT::dbo.Customer TO app_role;"
        )
        self.assertEqual(len(document.objects), 0)

    def test_standalone_go_is_a_batch_boundary_but_identifier_go_is_not(self) -> None:
        sql = (
            "CREATE VIEW dbo.FirstView AS SELECT * FROM dbo.SourceOne;\n"
            "GO\n"
            "CREATE VIEW dbo.SecondView AS SELECT * FROM dbo.[GO];\n"
            "GO\n"
        )
        document = SQLParser().parse(sql)

        self.assertEqual([obj.name for obj in document.objects], ["FirstView", "SecondView"])
        self.assertIn("GO", reference_names(document.objects[1]))


if __name__ == "__main__":
    unittest.main()
