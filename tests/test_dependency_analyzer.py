import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from sqlstudio import DependencyAnalyzer, DependencyKind


class DependencyAnalyzerTests(unittest.TestCase):
    def test_analyze_returns_graph_for_one_script(self):
        graph = DependencyAnalyzer().analyze(
            "CREATE VIEW dbo.ActiveOrders AS "
            "SELECT * FROM sales.Orders;"
        )

        self.assertIsNotNone(graph.get_node("dbo.ActiveOrders"))
        self.assertIsNotNone(graph.get_node("sales.Orders"))
        self.assertEqual(
            [node.name for node in graph.dependencies_of("dbo.ActiveOrders")],
            ["sales.Orders"],
        )

    def test_analyze_many_merges_documents(self):
        graph = DependencyAnalyzer().analyze_many(
            [
                "CREATE VIEW dbo.ActiveOrders AS SELECT * FROM sales.Orders;",
                "CREATE VIEW dbo.OrderCustomers AS SELECT * FROM crm.Customers;",
            ]
        )

        self.assertIsNotNone(graph.get_node("dbo.ActiveOrders"))
        self.assertIsNotNone(graph.get_node("dbo.OrderCustomers"))
        self.assertIsNotNone(graph.get_node("sales.Orders"))
        self.assertIsNotNone(graph.get_node("crm.Customers"))
        self.assertEqual(len(graph.edges), 2)

    def test_empty_sql_returns_empty_graph(self):
        graph = DependencyAnalyzer().analyze("   ")

        self.assertEqual(graph.nodes, ())
        self.assertEqual(graph.edges, ())

    def test_facade_preserves_dependency_kind(self):
        graph = DependencyAnalyzer().analyze(
            "CREATE PROCEDURE dbo.RunReport AS EXEC dbo.GenerateReport;"
        )

        execute_edges = [edge for edge in graph.edges if edge.kind is DependencyKind.EXECUTES]
        self.assertEqual(len(execute_edges), 1)


if __name__ == "__main__":
    unittest.main()
