import unittest

from sqlstudio.cross_reference import (
    CrossReferenceAnalyzer,
    CrossReferenceType,
)


class CrossReferenceAnalyzerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.analyzer = CrossReferenceAnalyzer()

    def test_analyze_returns_read_reference(self) -> None:
        references = self.analyzer.analyze(
            "CREATE VIEW dbo.ActiveOrders AS "
            "SELECT * FROM sales.Orders;"
        )

        self.assertEqual(len(references), 1)
        self.assertEqual(references[0].source, "dbo.ActiveOrders")
        self.assertEqual(references[0].target, "sales.Orders")
        self.assertEqual(
            references[0].reference_type,
            CrossReferenceType.READ,
        )

    def test_analyze_returns_execute_reference(self) -> None:
        references = self.analyzer.analyze(
            "CREATE PROCEDURE dbo.RunRefresh AS "
            "EXEC maintenance.RefreshCache;"
        )

        self.assertEqual(len(references), 1)
        self.assertEqual(references[0].source, "dbo.RunRefresh")
        self.assertEqual(references[0].target, "maintenance.RefreshCache")
        self.assertEqual(
            references[0].reference_type,
            CrossReferenceType.EXECUTE,
        )

    def test_analyze_many_merges_scripts(self) -> None:
        references = self.analyzer.analyze_many(
            [
                "CREATE VIEW dbo.V1 AS SELECT * FROM dbo.T1;",
                "CREATE VIEW dbo.V2 AS SELECT * FROM dbo.T2;",
            ]
        )

        self.assertEqual(
            [(item.source, item.target) for item in references],
            [("dbo.V1", "dbo.T1"), ("dbo.V2", "dbo.T2")],
        )

    def test_outgoing_filters_by_source(self) -> None:
        references = self.analyzer.outgoing(
            [
                "CREATE VIEW dbo.V1 AS SELECT * FROM dbo.T1;",
                "CREATE VIEW dbo.V2 AS SELECT * FROM dbo.T2;",
            ],
            "DBO.V1",
        )

        self.assertEqual(len(references), 1)
        self.assertEqual(references[0].target, "dbo.T1")

    def test_incoming_filters_by_target(self) -> None:
        references = self.analyzer.incoming(
            [
                "CREATE VIEW dbo.V1 AS SELECT * FROM dbo.Shared;",
                "CREATE VIEW dbo.V2 AS SELECT * FROM dbo.Shared;",
            ],
            "dbo.shared",
        )

        self.assertEqual(
            [item.source for item in references],
            ["dbo.V1", "dbo.V2"],
        )


if __name__ == "__main__":
    unittest.main()
