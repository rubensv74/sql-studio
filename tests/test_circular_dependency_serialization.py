import json
import tempfile
import unittest
from pathlib import Path

from sqlstudio.circular_dependencies import (
    CircularDependencyEngine,
    CircularDependencySerializer,
)
from sqlstudio.dependencies import DependencyGraph, DependencyNode


class CircularDependencySerializerTests(unittest.TestCase):
    def _cycles(self):
        graph = DependencyGraph()
        graph.add_dependency(DependencyNode("dbo.B"), DependencyNode("dbo.A"))
        graph.add_dependency(DependencyNode("dbo.A"), DependencyNode("dbo.B"))
        return CircularDependencyEngine().detect(graph)

    def test_to_dict_has_stable_contract(self):
        payload = CircularDependencySerializer.to_dict(self._cycles())

        self.assertEqual("1.0", payload["schema_version"])
        self.assertEqual({"cycle_count": 1, "object_count": 2}, payload["summary"])
        finding = payload["circular_dependencies"][0]
        self.assertEqual(["dbo.A", "dbo.B"], finding["members"])
        self.assertFalse(finding["is_self_reference"])
        self.assertEqual(
            [
                {"source": "dbo.A", "target": "dbo.B", "kind": "references"},
                {"source": "dbo.B", "target": "dbo.A", "kind": "references"},
            ],
            finding["edges"],
        )

    def test_compact_json_is_valid(self):
        payload = CircularDependencySerializer.to_json(self._cycles(), indent=None)
        self.assertEqual(1, json.loads(payload)["summary"]["cycle_count"])
        self.assertNotIn("\n", payload)

    def test_write_json_creates_parent_directory(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            destination = Path(temporary_directory) / "reports" / "cycles.json"
            result = CircularDependencySerializer.write_json(self._cycles(), destination)
            self.assertEqual(destination, result)
            self.assertTrue(destination.is_file())


if __name__ == "__main__":
    unittest.main()
