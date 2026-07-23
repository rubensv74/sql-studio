import unittest

from sqlstudio.cross_reference import (
    CrossReference,
    CrossReferenceEngine,
    CrossReferenceType,
)
from sqlstudio.dependencies import (
    DependencyGraph,
    DependencyKind,
    DependencyNode,
)


class CrossReferenceEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.graph = DependencyGraph()
        view = DependencyNode("dbo.ActiveOrders", "View")
        table = DependencyNode("sales.Orders", "Table")
        procedure = DependencyNode("dbo.RefreshOrders", "Procedure")
        helper = DependencyNode("dbo.RebuildOrderCache", "Procedure")

        self.graph.add_dependency(view, table, DependencyKind.REFERENCES)
        self.graph.add_dependency(procedure, table, DependencyKind.REFERENCES)
        self.graph.add_dependency(procedure, helper, DependencyKind.EXECUTES)
        self.engine = CrossReferenceEngine()

    def test_build_maps_dependency_kinds(self) -> None:
        self.assertEqual(
            self.engine.build(self.graph),
            (
                CrossReference(
                    "dbo.ActiveOrders",
                    "sales.Orders",
                    CrossReferenceType.READ,
                ),
                CrossReference(
                    "dbo.RefreshOrders",
                    "dbo.RebuildOrderCache",
                    CrossReferenceType.EXECUTE,
                ),
                CrossReference(
                    "dbo.RefreshOrders",
                    "sales.Orders",
                    CrossReferenceType.READ,
                ),
            ),
        )

    def test_outgoing_is_case_insensitive(self) -> None:
        references = self.engine.outgoing(self.graph, "DBO.REFRESHORDERS")
        self.assertEqual(len(references), 2)
        self.assertTrue(all(item.source == "dbo.RefreshOrders" for item in references))

    def test_incoming_returns_referencing_objects(self) -> None:
        references = self.engine.incoming(self.graph, "sales.Orders")
        self.assertEqual(
            {item.source for item in references},
            {"dbo.ActiveOrders", "dbo.RefreshOrders"},
        )

    def test_empty_object_name_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.engine.outgoing(self.graph, "   ")

    def test_duplicate_graph_edges_produce_one_reference(self) -> None:
        source = DependencyNode("dbo.One", "View")
        target = DependencyNode("dbo.Two", "Table")
        graph = DependencyGraph()
        graph.add_dependency(source, target)
        graph.add_dependency(source, target)
        self.assertEqual(len(self.engine.build(graph)), 1)


if __name__ == "__main__":
    unittest.main()
