import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from sqlstudio.dead_objects import DeadObjectEngine
from sqlstudio.dependencies import DependencyGraph, DependencyNode


class DeadObjectEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = DeadObjectEngine()

    @staticmethod
    def _member_names(result):
        return [
            tuple(member.name for member in finding.members)
            for finding in result.findings
        ]

    def test_unreferenced_source_is_candidate_but_dependency_is_not(self):
        graph = DependencyGraph()
        graph.add_dependency(
            DependencyNode("dbo.Entry", "Stored Procedure"),
            DependencyNode("dbo.Helper", "View"),
        )

        result = self.engine.detect(graph)

        self.assertEqual(self._member_names(result), [("dbo.Entry",)])
        self.assertEqual(result.defined_object_count, 2)

    def test_unknown_reference_only_node_is_never_candidate(self):
        graph = DependencyGraph()
        graph.add_dependency(
            DependencyNode("dbo.Entry", "Stored Procedure"),
            DependencyNode("external.Source", "Unknown"),
        )

        result = self.engine.detect(graph)

        self.assertEqual(self._member_names(result), [("dbo.Entry",)])
        self.assertEqual(result.defined_object_count, 1)

    def test_self_reference_is_a_single_circular_candidate(self):
        graph = DependencyGraph()
        node = DependencyNode("dbo.RecursiveView", "View")
        graph.add_dependency(node, node)

        result = self.engine.detect(graph)

        self.assertEqual(self._member_names(result), [("dbo.RecursiveView",)])
        self.assertTrue(result.findings[0].is_circular_component)

    def test_isolated_cycle_is_reported_as_one_candidate_component(self):
        graph = DependencyGraph()
        a = DependencyNode("dbo.A", "View")
        b = DependencyNode("dbo.B", "View")
        graph.add_dependency(a, b)
        graph.add_dependency(b, a)

        result = self.engine.detect(graph)

        self.assertEqual(self._member_names(result), [("dbo.A", "dbo.B")])
        self.assertTrue(result.findings[0].is_circular_component)

    def test_cycle_with_external_incoming_reference_is_not_candidate(self):
        graph = DependencyGraph()
        a = DependencyNode("dbo.A", "View")
        b = DependencyNode("dbo.B", "View")
        caller = DependencyNode("dbo.Caller", "Stored Procedure")
        graph.add_dependency(a, b)
        graph.add_dependency(b, a)
        graph.add_dependency(caller, a)

        result = self.engine.detect(graph)

        self.assertEqual(self._member_names(result), [("dbo.Caller",)])

    def test_trigger_root_is_excluded_as_implicit_entry_object(self):
        graph = DependencyGraph()
        graph.add_node(DependencyNode("dbo.trg_Orders", "Trigger"))

        result = self.engine.detect(graph)

        self.assertEqual(result.findings, ())
        self.assertEqual(len(result.excluded_objects), 1)
        self.assertEqual(
            result.excluded_objects[0].reason,
            "component_contains_implicit_entry_object",
        )

    def test_declared_entry_point_excludes_its_root_component(self):
        graph = DependencyGraph()
        graph.add_dependency(
            DependencyNode("dbo.Run", "Stored Procedure"),
            DependencyNode("dbo.Helper", "Function"),
        )

        result = self.engine.detect(graph, entry_points=["DBO.RUN"])

        self.assertEqual(result.findings, ())
        self.assertEqual(result.entry_points, ("dbo.Run",))
        self.assertEqual(result.excluded_objects[0].name, "dbo.Run")
        self.assertEqual(
            result.excluded_objects[0].reason,
            "component_contains_declared_entry_point",
        )

    def test_unknown_declared_entry_point_is_rejected(self):
        graph = DependencyGraph()
        graph.add_node(DependencyNode("dbo.Run", "Stored Procedure"))

        with self.assertRaisesRegex(ValueError, "not a defined SQL object"):
            self.engine.detect(graph, entry_points=["dbo.Missing"])


if __name__ == "__main__":
    unittest.main()
