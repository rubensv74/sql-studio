import unittest

from sqlstudio.circular_dependencies import CircularDependencyEngine
from sqlstudio.dependencies import DependencyGraph, DependencyNode


class CircularDependencyEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = CircularDependencyEngine()

    def _graph(self, edges):
        graph = DependencyGraph()
        for source, target in edges:
            graph.add_dependency(DependencyNode(source), DependencyNode(target))
        return graph

    def test_acyclic_graph_returns_no_cycles(self):
        graph = self._graph([("dbo.A", "dbo.B"), ("dbo.B", "dbo.C")])
        self.assertEqual((), self.engine.detect(graph))

    def test_detects_two_object_cycle(self):
        graph = self._graph([("dbo.A", "dbo.B"), ("dbo.B", "dbo.A")])
        cycles = self.engine.detect(graph)
        self.assertEqual(1, len(cycles))
        self.assertEqual(("dbo.A", "dbo.B"), cycles[0].members)

    def test_detects_multihop_cycle_as_one_component(self):
        graph = self._graph(
            [
                ("dbo.A", "dbo.B"),
                ("dbo.B", "dbo.C"),
                ("dbo.C", "dbo.A"),
                ("dbo.A", "dbo.C"),
            ]
        )
        cycles = self.engine.detect(graph)
        self.assertEqual(1, len(cycles))
        self.assertEqual(("dbo.A", "dbo.B", "dbo.C"), cycles[0].members)
        self.assertEqual(4, len(cycles[0].edges))

    def test_detects_self_reference(self):
        graph = self._graph([("dbo.A", "dbo.A")])
        cycles = self.engine.detect(graph)
        self.assertEqual(1, len(cycles))
        self.assertEqual(("dbo.A",), cycles[0].members)
        self.assertTrue(cycles[0].is_self_reference)

    def test_ignores_disconnected_acyclic_components(self):
        graph = self._graph(
            [
                ("dbo.A", "dbo.B"),
                ("dbo.B", "dbo.A"),
                ("dbo.X", "dbo.Y"),
            ]
        )
        cycles = self.engine.detect(graph)
        self.assertEqual(1, len(cycles))
        self.assertEqual(("dbo.A", "dbo.B"), cycles[0].members)

    def test_detection_is_case_insensitive_and_preserves_canonical_name(self):
        graph = self._graph([("dbo.Alpha", "dbo.Beta"), ("DBO.BETA", "DBO.ALPHA")])
        cycles = self.engine.detect(graph)
        self.assertEqual(1, len(cycles))
        self.assertEqual(("dbo.Alpha", "dbo.Beta"), cycles[0].members)

    def test_multiple_cycles_are_sorted_deterministically(self):
        graph = self._graph(
            [
                ("dbo.Z", "dbo.Y"),
                ("dbo.Y", "dbo.Z"),
                ("dbo.B", "dbo.A"),
                ("dbo.A", "dbo.B"),
            ]
        )
        cycles = self.engine.detect(graph)
        self.assertEqual(
            [("dbo.A", "dbo.B"), ("dbo.Y", "dbo.Z")],
            [cycle.members for cycle in cycles],
        )


if __name__ == "__main__":
    unittest.main()
