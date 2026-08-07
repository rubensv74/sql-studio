import unittest

from sqlstudio.circular_dependencies import CircularDependencyAnalyzer


class CircularDependencyAnalyzerTests(unittest.TestCase):
    def test_analyze_many_detects_cycle_across_files(self):
        sql_texts = [
            "CREATE VIEW dbo.A AS SELECT * FROM dbo.B;",
            "CREATE VIEW dbo.B AS SELECT * FROM dbo.A;",
        ]

        cycles = CircularDependencyAnalyzer().analyze_many(sql_texts)

        self.assertEqual(1, len(cycles))
        self.assertEqual(("dbo.A", "dbo.B"), cycles[0].members)

    def test_analyze_many_returns_empty_for_acyclic_sql(self):
        sql_texts = [
            "CREATE VIEW dbo.A AS SELECT * FROM dbo.B;",
            "CREATE VIEW dbo.B AS SELECT * FROM dbo.C;",
        ]
        self.assertEqual((), CircularDependencyAnalyzer().analyze_many(sql_texts))


if __name__ == "__main__":
    unittest.main()
