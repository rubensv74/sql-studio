import unittest

from sqlstudio.dependencies import DependencyGraph, DependencyNode
from sqlstudio.impact_analysis import ImpactAnalysisEngine


class TestImpactAnalysisEngine(unittest.TestCase):
    def setUp(self):
        self.graph = DependencyGraph()
        self.graph.add_dependency(DependencyNode("A"), DependencyNode("B"))
        self.graph.add_dependency(DependencyNode("B"), DependencyNode("C"))
        self.graph.add_dependency(DependencyNode("C"), DependencyNode("A"))
        self.graph.add_dependency(DependencyNode("B"), DependencyNode("D"))

    def test_analyze_returns_transitive_dependencies_once(self):
        result = ImpactAnalysisEngine().analyze(self.graph, "A")

        self.assertEqual("A", result.root_object)
        self.assertEqual(["A", "B", "C", "D"], result.impacted_objects)

    def test_analyze_builds_real_multilevel_tree(self):
        result = ImpactAnalysisEngine().analyze(self.graph, "A")

        self.assertIsNotNone(result.tree)
        self.assertEqual("A", result.tree.name)
        self.assertEqual(["B"], [node.name for node in result.tree.children])
        self.assertEqual(
            ["C", "D"],
            [node.name for node in result.tree.children[0].children],
        )
        self.assertEqual([], result.tree.children[0].children[0].children)

    def test_matching_is_case_insensitive_and_preserves_graph_casing(self):
        result = ImpactAnalysisEngine().analyze(self.graph, "a")

        self.assertEqual("A", result.root_object)
        self.assertEqual("A", result.tree.name)

    def test_unknown_root_is_returned_as_is(self):
        result = ImpactAnalysisEngine().analyze(self.graph, "dbo.Unknown")

        self.assertEqual("dbo.Unknown", result.root_object)
        self.assertEqual(["dbo.Unknown"], result.impacted_objects)
        self.assertEqual([], result.tree.children)

    def test_rejects_empty_root(self):
        with self.assertRaisesRegex(ValueError, "root_object"):
            ImpactAnalysisEngine().analyze(self.graph, "   ")


if __name__ == "__main__":
    unittest.main()
