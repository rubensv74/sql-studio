import unittest
from unittest.mock import Mock, patch

from sqlstudio.impact_analysis.analyzer import ImpactAnalyzer


class TestImpactAnalyzer(unittest.TestCase):
    @patch("sqlstudio.impact_analysis.analyzer.ImpactAnalysisEngine")
    @patch("sqlstudio.impact_analysis.analyzer.DependencyAnalyzer")
    def test_analyze_builds_graph_and_delegates_to_engine(
        self,
        dependency_analyzer_class,
        impact_engine_class,
    ):
        graph = object()
        expected = object()
        dependency_analyzer_class.return_value.analyze.return_value = graph
        impact_engine_class.return_value.analyze.return_value = expected

        analyzer = ImpactAnalyzer()
        result = analyzer.analyze("SELECT * FROM dbo.Source;", "dbo.Source")

        dependency_analyzer_class.return_value.analyze.assert_called_once_with(
            "SELECT * FROM dbo.Source;"
        )
        impact_engine_class.return_value.analyze.assert_called_once_with(
            graph,
            "dbo.Source",
        )
        self.assertIs(result, expected)

    @patch("sqlstudio.impact_analysis.analyzer.ImpactAnalysisEngine")
    @patch("sqlstudio.impact_analysis.analyzer.DependencyAnalyzer")
    def test_analyze_many_builds_combined_graph_and_delegates_to_engine(
        self,
        dependency_analyzer_class,
        impact_engine_class,
    ):
        sql_texts = [
            "CREATE VIEW dbo.A AS SELECT 1 AS Value;",
            "CREATE VIEW dbo.B AS SELECT * FROM dbo.A;",
        ]
        graph = object()
        expected = object()
        dependency_analyzer_class.return_value.analyze_many.return_value = graph
        impact_engine_class.return_value.analyze.return_value = expected

        analyzer = ImpactAnalyzer()
        result = analyzer.analyze_many(sql_texts, "dbo.A")

        dependency_analyzer_class.return_value.analyze_many.assert_called_once_with(
            sql_texts
        )
        impact_engine_class.return_value.analyze.assert_called_once_with(
            graph,
            "dbo.A",
        )
        self.assertIs(result, expected)

    @patch("sqlstudio.impact_analysis.analyzer.ImpactAnalysisEngine")
    @patch("sqlstudio.impact_analysis.analyzer.DependencyAnalyzer")
    def test_reuses_collaborators_between_calls(
        self,
        dependency_analyzer_class,
        impact_engine_class,
    ):
        dependency_analyzer_class.return_value.analyze.return_value = object()

        analyzer = ImpactAnalyzer()
        analyzer.analyze("SELECT 1;", "dbo.A")
        analyzer.analyze("SELECT 2;", "dbo.B")

        dependency_analyzer_class.assert_called_once_with()
        impact_engine_class.assert_called_once_with()
        self.assertEqual(
            dependency_analyzer_class.return_value.analyze.call_count,
            2,
        )
        self.assertEqual(
            impact_engine_class.return_value.analyze.call_count,
            2,
        )

    @patch("sqlstudio.impact_analysis.analyzer.ImpactAnalysisEngine")
    @patch("sqlstudio.impact_analysis.analyzer.DependencyAnalyzer")
    def test_propagates_dependency_analyzer_errors(
        self,
        dependency_analyzer_class,
        impact_engine_class,
    ):
        dependency_analyzer_class.return_value.analyze.side_effect = ValueError(
            "invalid SQL"
        )

        analyzer = ImpactAnalyzer()

        with self.assertRaisesRegex(ValueError, "invalid SQL"):
            analyzer.analyze("INVALID", "dbo.Source")

        impact_engine_class.return_value.analyze.assert_not_called()


if __name__ == "__main__":
    unittest.main()
