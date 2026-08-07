import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from sqlstudio.parser import SQLParser
from sqlstudio.rules import StaticAnalysisAnalyzer


class _CountingParser(SQLParser):
    def __init__(self) -> None:
        super().__init__()
        self.calls = 0

    def parse(self, sql_text: str):
        self.calls += 1
        return super().parse(sql_text)


class StaticAnalysisAnalyzerTests(unittest.TestCase):
    def test_parses_each_source_once_for_all_default_rules(self):
        parser = _CountingParser()
        analyzer = StaticAnalysisAnalyzer(parser=parser)
        result = analyzer.analyze_many(
            [
                "CREATE PROCEDURE dbo.Entry AS EXEC dbo.Helper;",
                "CREATE PROCEDURE dbo.Helper AS SELECT 1;",
                "CREATE PROCEDURE dbo.Orphan AS SELECT 1;",
            ],
            entry_points=["dbo.Entry"],
        )
        self.assertEqual(parser.calls, 3)
        self.assertEqual(tuple(f.rule_id for f in result.findings), ("SQL002",))
        self.assertEqual(result.findings[0].objects, ("dbo.Orphan",))

    def test_rule_selection_can_run_cycle_detection_only(self):
        result = StaticAnalysisAnalyzer().analyze_many(
            [
                "CREATE PROCEDURE dbo.A AS EXEC dbo.B;",
                "CREATE PROCEDURE dbo.B AS EXEC dbo.A;",
            ],
            rule_ids=["sql001"],
        )
        self.assertEqual(tuple(r.rule_id for r in result.rule_results), ("SQL001",))
        self.assertEqual(len(result.findings), 1)
        self.assertEqual(result.findings[0].severity.value, "error")

    def test_dynamic_sql_is_reported_once_in_shared_context(self):
        result = StaticAnalysisAnalyzer().analyze(
            "CREATE PROCEDURE dbo.Dynamic AS EXEC sp_executesql N'SELECT 1';",
            entry_points=["dbo.Dynamic"],
        )
        self.assertEqual(result.dynamic_sql_object_count, 1)

    def test_entry_points_are_deduplicated_case_insensitively(self):
        result = StaticAnalysisAnalyzer().analyze(
            "CREATE PROCEDURE dbo.Entry AS SELECT 1;",
            entry_points=["dbo.Entry", "DBO.ENTRY"],
            rule_ids=["SQL002"],
        )
        self.assertEqual(result.entry_points, ("dbo.Entry",))
        self.assertEqual(result.findings, ())


if __name__ == "__main__":
    unittest.main()
