import unittest

from sqlstudio.dependencies import DependencyGraph, DependencyNode
from sqlstudio.impact_analysis import ImpactAnalysisEngine


class TestImpactAnalysisEngine(unittest.TestCase):
    def setUp(self):
        self.graph = DependencyGraph()
        self.graph.add_dependency(
            DependencyNode("dbo.ViewA"),
            DependencyNode("dbo.Table"),
        )
        self.graph.add_dependency(
            DependencyNode("dbo.ProcB"),
            DependencyNode("dbo.ViewA"),
        )
        self.graph.add_dependency(
            DependencyNode("dbo.ProcC"),
            DependencyNode("dbo.Table"),
        )
        # Close a cycle without changing the expected impact semantics.
        self.graph.add_dependency(
            DependencyNode("dbo.Table"),
            DependencyNode("dbo.ProcB"),
        )

    def test_analyze_returns_transitive_dependents_once(self):
        result = ImpactAnalysisEngine().analyze(self.graph, "dbo.Table")

        self.assertEqual("dbo.Table", result.root_object)
        self.assertEqual(
            ["dbo.Table", "dbo.ProcC", "dbo.ViewA", "dbo.ProcB"],
            result.impacted_objects,
        )

    def test_analyze_builds_real_multilevel_impact_tree(self):
        result = ImpactAnalysisEngine().analyze(self.graph, "dbo.Table")

        self.assertIsNotNone(result.tree)
        self.assertEqual("dbo.Table", result.tree.name)
        self.assertEqual(
            ["dbo.ProcC", "dbo.ViewA"],
            [node.name for node in result.tree.children],
        )
        self.assertEqual(
            ["dbo.ProcB"],
            [node.name for node in result.tree.children[1].children],
        )
        self.assertEqual(
            [],
            result.tree.children[1].children[0].children,
        )

    def test_impact_does_not_follow_outgoing_dependencies(self):
        result = ImpactAnalysisEngine().analyze(self.graph, "dbo.ProcC")

        self.assertEqual(["dbo.ProcC"], result.impacted_objects)

    def test_matching_is_case_insensitive_and_preserves_graph_casing(self):
        result = ImpactAnalysisEngine().analyze(self.graph, "DBO.TABLE")

        self.assertEqual("dbo.Table", result.root_object)
        self.assertEqual("dbo.Table", result.tree.name)

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
