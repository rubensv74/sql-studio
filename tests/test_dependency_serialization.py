import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from sqlstudio.dependencies import (
    DependencyGraph,
    DependencyGraphSerializer,
    DependencyKind,
    DependencyNode,
)


class DependencyGraphSerializerTests(unittest.TestCase):
    def build_graph(self) -> DependencyGraph:
        graph = DependencyGraph()
        graph.add_dependency(
            DependencyNode("dbo.usp_LoadOrders", "Stored Procedure"),
            DependencyNode("sales.Orders", "Table"),
            DependencyKind.REFERENCES,
        )
        graph.add_dependency(
            DependencyNode("dbo.usp_LoadOrders", "Stored Procedure"),
            DependencyNode("dbo.usp_AuditLoad", "Stored Procedure"),
            DependencyKind.EXECUTES,
        )
        return graph

    def test_to_dict_contains_version_nodes_and_edges(self):
        payload = DependencyGraphSerializer.to_dict(self.build_graph())

        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(
            payload["nodes"],
            [
                {"name": "dbo.usp_AuditLoad", "object_type": "Stored Procedure"},
                {"name": "dbo.usp_LoadOrders", "object_type": "Stored Procedure"},
                {"name": "sales.Orders", "object_type": "Table"},
            ],
        )
        self.assertEqual(
            payload["edges"],
            [
                {
                    "source": "dbo.usp_LoadOrders",
                    "target": "dbo.usp_AuditLoad",
                    "kind": "executes",
                },
                {
                    "source": "dbo.usp_LoadOrders",
                    "target": "sales.Orders",
                    "kind": "references",
                },
            ],
        )

    def test_to_json_is_valid_and_deterministic(self):
        graph = self.build_graph()

        first = DependencyGraphSerializer.to_json(graph)
        second = DependencyGraphSerializer.to_json(graph)

        self.assertEqual(first, second)
        self.assertEqual(json.loads(first), DependencyGraphSerializer.to_dict(graph))

    def test_compact_json_can_be_requested(self):
        text = DependencyGraphSerializer.to_json(self.build_graph(), indent=None)

        self.assertNotIn("\n", text)
        self.assertEqual(json.loads(text)["schema_version"], 1)

    def test_write_json_creates_parent_directory_and_trailing_newline(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            destination = Path(temporary_directory) / "reports" / "dependencies.json"

            written_path = DependencyGraphSerializer.write_json(
                self.build_graph(),
                destination,
            )

            self.assertEqual(written_path, destination)
            self.assertTrue(destination.exists())
            self.assertTrue(destination.read_text(encoding="utf-8").endswith("\n"))
            self.assertEqual(
                json.loads(destination.read_text(encoding="utf-8")),
                DependencyGraphSerializer.to_dict(self.build_graph()),
            )


if __name__ == "__main__":
    unittest.main()
