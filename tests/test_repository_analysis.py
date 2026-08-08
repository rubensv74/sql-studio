from __future__ import annotations

import json
import unittest

from sqlstudio.parser import SQLParser
from sqlstudio.repository_analysis import (
    RepositoryAnalysisEngine,
    RepositoryAnalysisReportGenerator,
    RepositoryAnalysisSerializer,
)
from sqlstudio.source import SqlSource


class CountingParser(SQLParser):
    def __init__(self) -> None:
        super().__init__()
        self.source_calls: list[str] = []

    def parse_source(self, source: SqlSource):
        self.source_calls.append(source.source_id)
        return super().parse_source(source)


class RepositoryAnalysisTests(unittest.TestCase):
    def setUp(self) -> None:
        self.sources = (
            SqlSource(
                "sql/a.sql",
                "CREATE VIEW dbo.A AS SELECT * FROM dbo.B;",
                path="sql/a.sql",
            ),
            SqlSource(
                "sql/b.sql",
                "CREATE VIEW dbo.B AS SELECT * FROM dbo.A;",
                path="sql/b.sql",
            ),
            SqlSource(
                "sql/orphan.sql",
                "CREATE VIEW dbo.Orphan AS SELECT 1 AS Value;",
                path="sql/orphan.sql",
            ),
            SqlSource(
                "sql/<dynamic>.sql",
                "DECLARE @sql nvarchar(max) = N'SELECT 1'; EXEC sp_executesql @sql;",
                path="sql/<dynamic>.sql",
            ),
        )

    def test_master_engine_parses_each_source_once(self) -> None:
        parser = CountingParser()
        result = RepositoryAnalysisEngine(parser=parser).analyze(self.sources)

        self.assertEqual(
            parser.source_calls,
            [
                "sql/<dynamic>.sql",
                "sql/a.sql",
                "sql/b.sql",
                "sql/orphan.sql",
            ],
        )
        self.assertEqual(result.source_count, 4)
        self.assertEqual(result.parsed_object_count, 4)

    def test_source_provenance_and_graph_direction_are_preserved(self) -> None:
        result = RepositoryAnalysisEngine().analyze(self.sources)
        by_name = {item.name: item for item in result.objects}

        self.assertEqual(by_name["dbo.A"].source_id, "sql/a.sql")
        self.assertEqual(by_name["dbo.B"].source_id, "sql/b.sql")
        self.assertEqual(by_name["dbo.A"].dependencies, ("dbo.B",))
        self.assertEqual(by_name["dbo.A"].dependents, ("dbo.B",))
        self.assertIn("script:sql/<dynamic>.sql", by_name)
        self.assertTrue(by_name["script:sql/<dynamic>.sql"].dynamic_sql)

    def test_cycles_dead_candidates_and_rules_share_the_same_graph(self) -> None:
        result = RepositoryAnalysisEngine().analyze(self.sources)

        self.assertEqual(len(result.cycles), 1)
        self.assertEqual(result.cycles[0].members, ("dbo.A", "dbo.B"))
        dead_components = {
            tuple(member.name for member in finding.members)
            for finding in result.dead_objects.findings
        }
        self.assertIn(("dbo.A", "dbo.B"), dead_components)
        self.assertIn(("dbo.Orphan",), dead_components)
        self.assertNotIn(("script:sql/<dynamic>.sql",), dead_components)
        self.assertEqual(
            {finding.rule_id for finding in result.static_analysis.findings},
            {"SQL001", "SQL002"},
        )

    def test_json_schema_1_is_deterministic_and_complete(self) -> None:
        result = RepositoryAnalysisEngine().analyze(self.sources)
        first = RepositoryAnalysisSerializer.to_json(result)
        second = RepositoryAnalysisSerializer.to_json(result)
        payload = json.loads(first)

        self.assertEqual(first, second)
        self.assertEqual(payload["schema_version"], "1.0")
        self.assertEqual(payload["summary"]["source_count"], 4)
        self.assertEqual(payload["summary"]["circular_component_count"], 1)
        self.assertEqual(payload["summary"]["dynamic_sql_object_count"], 1)
        self.assertEqual(payload["context"]["dependency_direction"], "source -> target")
        self.assertTrue(payload["context"]["dead_objects_are_candidates_only"])
        self.assertTrue(payload["uncertainty"]["static_analysis_only"])
        self.assertIn("script:sql/<dynamic>.sql", payload["uncertainty"]["dynamic_sql_objects"])

    def test_html_is_self_contained_escaped_and_has_required_sections(self) -> None:
        result = RepositoryAnalysisEngine().analyze(self.sources)
        html = RepositoryAnalysisReportGenerator().generate(result)

        self.assertIn("Análisis del repositorio", html)
        self.assertIn("Inventario del repositorio", html)
        self.assertIn("Mapa de dependencias", html)
        self.assertIn("Objetos clave", html)
        self.assertIn("Dependencias circulares", html)
        self.assertIn("Candidatos a objetos no utilizados", html)
        self.assertIn("Hallazgos por severidad", html)
        self.assertIn("SQL dinámico e incertidumbre", html)
        self.assertIn("Explorador de objetos", html)
        self.assertIn("Trazabilidad de fuentes", html)
        self.assertIn("sql/&lt;dynamic&gt;.sql", html)
        self.assertNotIn("https://cdn", html)
        self.assertNotIn("<script src=", html)

    def test_duplicate_source_ids_are_rejected_case_insensitively(self) -> None:
        with self.assertRaisesRegex(ValueError, "Duplicate SQL source id"):
            RepositoryAnalysisEngine().analyze(
                (
                    SqlSource("sql/a.sql", "SELECT 1;"),
                    SqlSource("SQL/A.SQL", "SELECT 2;"),
                )
            )


if __name__ == "__main__":
    unittest.main()
