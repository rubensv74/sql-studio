import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from sqlstudio.dependencies import DependencyKind, DependencyResolver
from sqlstudio.parser.ast import Reference, SqlDocument, SqlObject


class DependencyResolverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.resolver = DependencyResolver()

    def test_resolves_object_and_reference_nodes(self):
        document = SqlDocument(
            sql_text="",
            objects=[
                SqlObject(
                    name="Report",
                    schema="dbo",
                    object_type="View",
                    references=[Reference(name="Orders", schema="sales")],
                )
            ],
        )

        graph = self.resolver.resolve(document)

        self.assertIsNotNone(graph.get_node("dbo.Report"))
        self.assertIsNotNone(graph.get_node("sales.Orders"))
        self.assertEqual(
            tuple(node.name for node in graph.dependencies_of("dbo.Report")),
            ("sales.Orders",),
        )

    def test_preserves_cross_database_reference_name(self):
        document = SqlDocument(
            sql_text="",
            objects=[
                SqlObject(
                    name="Sync",
                    schema="etl",
                    object_type="Stored Procedure",
                    references=[Reference(name="Customer", schema="dbo", database="CRM")],
                )
            ],
        )

        graph = self.resolver.resolve(document)

        self.assertIsNotNone(graph.get_node("CRM.dbo.Customer"))

    def test_maps_call_references_to_executes_edges(self):
        document = SqlDocument(
            sql_text="",
            objects=[
                SqlObject(
                    name="Runner",
                    schema="dbo",
                    object_type="Stored Procedure",
                    references=[Reference(name="ChildProc", schema="dbo", kind="call")],
                )
            ],
        )

        graph = self.resolver.resolve(document)

        self.assertEqual(len(graph.edges), 1)
        self.assertEqual(graph.edges[0].kind, DependencyKind.EXECUTES)

    def test_resolves_multiple_documents_into_one_graph(self):
        documents = [
            SqlDocument(sql_text="", objects=[SqlObject(name="A", schema="dbo")]),
            SqlDocument(
                sql_text="",
                objects=[SqlObject(name="B", schema="dbo", references=[Reference(name="A", schema="dbo")])],
            ),
        ]

        graph = self.resolver.resolve(documents)

        self.assertEqual({node.name for node in graph.nodes}, {"dbo.A", "dbo.B"})
        self.assertEqual(tuple(node.name for node in graph.dependencies_of("dbo.B")), ("dbo.A",))

    def test_definition_metadata_wins_when_reference_appears_first(self):
        documents = [
            SqlDocument(
                sql_text="",
                objects=[
                    SqlObject(
                        name="B",
                        schema="dbo",
                        object_type="View",
                        references=[Reference(name="A", schema="dbo")],
                    )
                ],
            ),
            SqlDocument(
                sql_text="",
                objects=[SqlObject(name="A", schema="dbo", object_type="Table")],
            ),
        ]

        graph = self.resolver.resolve(documents)

        node = graph.get_node("dbo.A")
        self.assertIsNotNone(node)
        self.assertEqual(node.object_type, "Table")
        self.assertEqual(graph.edges[0].target.object_type, "Table")

    def test_empty_document_returns_empty_graph(self):
        graph = self.resolver.resolve(SqlDocument(sql_text=""))

        self.assertEqual(graph.nodes, ())
        self.assertEqual(graph.edges, ())


if __name__ == "__main__":
    unittest.main()
