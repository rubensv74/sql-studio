from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from sqlstudio import DependencyAnalyzer, SQLParser, SqlSource
from sqlstudio.cli import analyze_dependencies


FIXTURES = Path(__file__).resolve().parent / "fixtures" / "real_repository"


class SqlSourceIdentityTests(unittest.TestCase):
    def test_source_id_is_slash_normalized(self) -> None:
        source = SqlSource(r".\sql\import\seed.sql", "SELECT 1;")
        self.assertEqual(source.source_id, "sql/import/seed.sql")
        self.assertEqual(source.script_object_name, "script:sql/import/seed.sql")

    def test_raw_text_parser_keeps_legacy_unnamed_script(self) -> None:
        document = SQLParser().parse("SELECT * FROM dbo.LegacyTarget;")
        self.assertEqual(document.objects[0].name, "UnnamedScript")
        self.assertEqual(document.objects[0].object_type, "Script")

    def test_source_parser_assigns_physical_identity_only_to_scripts(self) -> None:
        parser = SQLParser()
        script = parser.parse_source(
            SqlSource("sql/import/seed.sql", "SELECT * FROM dbo.Target;")
        )
        durable = parser.parse_source(
            SqlSource(
                "sql/views/report.sql",
                "CREATE VIEW dbo.Report AS SELECT * FROM dbo.Target;",
            )
        )

        self.assertEqual(script.objects[0].name, "script:sql/import/seed.sql")
        self.assertEqual(script.objects[0].object_type, "Script")
        self.assertEqual(durable.objects[0].name, "Report")
        self.assertEqual(durable.objects[0].schema, "dbo")
        self.assertEqual(durable.objects[0].object_type, "View")

    def test_source_parser_consolidates_fallback_scopes_into_one_physical_script(self) -> None:
        sql = (FIXTURES / "multi_scope_physical_script.sql").read_text(encoding="utf-8")
        document = SQLParser().parse_source(
            SqlSource("sql/import/foundations.sql", sql)
        )

        scripts = [item for item in document.objects if item.object_type == "Script"]
        durable = [item for item in document.objects if item.object_type != "Script"]

        self.assertEqual(len(scripts), 1)
        self.assertEqual(scripts[0].name, "script:sql/import/foundations.sql")
        self.assertEqual([(item.schema, item.name) for item in durable], [("dbo", "LocalTable")])
        self.assertEqual(
            {(reference.schema, reference.name) for reference in scripts[0].references},
            {(None, "sp_executesql"), ("dbo", "AfterTarget"), ("dbo", "BeforeTarget")},
        )
        self.assertTrue(scripts[0].dynamic_sql)

    def test_two_physical_scripts_do_not_collapse_in_dependency_graph(self) -> None:
        graph = DependencyAnalyzer().analyze_sources(
            [
                SqlSource("sql/import/seed_a.sql", "SELECT * FROM dbo.TableA;"),
                SqlSource("sql/import/seed_b.sql", "SELECT * FROM dbo.TableB;"),
            ]
        )

        self.assertEqual(
            {node.name for node in graph.dependencies_of("script:sql/import/seed_a.sql")},
            {"dbo.TableA"},
        )
        self.assertEqual(
            {node.name for node in graph.dependencies_of("script:sql/import/seed_b.sql")},
            {"dbo.TableB"},
        )
        self.assertIsNotNone(graph.get_node("script:sql/import/seed_a.sql"))
        self.assertIsNotNone(graph.get_node("script:sql/import/seed_b.sql"))

    def test_cli_preserves_distinct_file_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            first = root / "first.sql"
            second = root / "second.sql"
            first.write_text("SELECT * FROM dbo.FirstTarget;", encoding="utf-8")
            second.write_text("SELECT * FROM dbo.SecondTarget;", encoding="utf-8")
            stdout = StringIO()

            with redirect_stdout(stdout):
                analyze_dependencies([str(first), str(second)])

            payload = json.loads(stdout.getvalue())
            script_nodes = {
                node["name"]
                for node in payload["nodes"]
                if node["object_type"] == "Script"
            }
            self.assertEqual(len(script_nodes), 2)
            self.assertTrue(all(name.startswith("script:") for name in script_nodes))
            script_edges = [
                edge
                for edge in payload["edges"]
                if edge["source"] in script_nodes
            ]
            self.assertEqual(
                {edge["target"] for edge in script_edges},
                {"dbo.FirstTarget", "dbo.SecondTarget"},
            )


if __name__ == "__main__":
    unittest.main()
