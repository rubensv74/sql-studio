import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from sqlstudio.dead_objects import DeadObjectAnalyzer


class DeadObjectAnalyzerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.analyzer = DeadObjectAnalyzer()

    def test_analyze_many_preserves_definition_metadata_across_file_order(self):
        sql_b = "CREATE VIEW dbo.B AS SELECT * FROM dbo.A;"
        sql_a = "CREATE TABLE dbo.A (Id int);"

        result = self.analyzer.analyze_many([sql_b, sql_a])

        self.assertEqual(len(result.findings), 1)
        self.assertEqual(result.findings[0].members[0].name, "dbo.B")
        self.assertEqual(result.findings[0].members[0].object_type, "View")
        self.assertEqual(result.defined_object_count, 2)

    def test_reports_dynamic_sql_uncertainty(self):
        sql = """
        CREATE PROCEDURE dbo.DynamicRunner
        AS
        BEGIN
            EXEC sp_executesql N'SELECT 1';
        END;
        """

        result = self.analyzer.analyze(sql)

        self.assertEqual(result.dynamic_sql_object_count, 1)


if __name__ == "__main__":
    unittest.main()
