import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from sqlstudio.dependencies import (
    DependencyGraph,
    DependencyKind,
    DependencyNode,
)


class DependencyGraphTests(unittest.TestCase):
    def test_add_dependency_registers_nodes_and_edge(self):
        graph = DependencyGraph()
        source = DependencyNode("dbo.usp_LoadOrders", "Stored Procedure")
        target = DependencyNode("dbo.Orders", "Table")

        edge = graph.add_dependency(source, target)

        self.assertEqual(graph.nodes, (target, source))
        self.assertEqual(graph.edges, (edge,))
        self.assertEqual(graph.dependencies_of(source.name), (target,))
        self.assertEqual(graph.dependents_of(target.name), (source,))

    def test_node_lookup_is_case_insensitive(self):
        graph = DependencyGraph()
        node = graph.add_node(DependencyNode("dbo.SampleView", "View"))

        self.assertIs(graph.get_node("DBO.SAMPLEVIEW"), node)

    def test_duplicate_dependency_is_not_repeated(self):
        graph = DependencyGraph()
        source = DependencyNode("dbo.Source", "View")
        target = DependencyNode("dbo.Target", "Table")

        graph.add_dependency(source, target)
        graph.add_dependency(source, target)

        self.assertEqual(len(graph.nodes), 2)
        self.assertEqual(len(graph.edges), 1)

    def test_dependency_kind_is_preserved(self):
        graph = DependencyGraph()
        graph.add_dependency(
            DependencyNode("dbo.Caller", "Stored Procedure"),
            DependencyNode("dbo.Callee", "Stored Procedure"),
            DependencyKind.EXECUTES,
        )

        self.assertEqual(graph.edges[0].kind, DependencyKind.EXECUTES)

    def test_empty_node_name_is_rejected(self):
        with self.assertRaises(ValueError):
            DependencyNode("   ")


if __name__ == "__main__":
    unittest.main()
