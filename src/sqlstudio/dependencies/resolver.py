from __future__ import annotations

from collections.abc import Iterable

from sqlstudio.parser.ast import Reference, SqlDocument, SqlObject

from .graph import DependencyGraph
from .models import DependencyKind, DependencyNode


class DependencyResolver:
    """Build a dependency graph from parsed SQL documents."""

    def resolve(self, documents: SqlDocument | Iterable[SqlDocument]) -> DependencyGraph:
        graph = DependencyGraph()
        document_iterable = [documents] if isinstance(documents, SqlDocument) else documents

        for document in document_iterable:
            self._add_document(graph, document)

        return graph

    def _add_document(self, graph: DependencyGraph, document: SqlDocument) -> None:
        for sql_object in document.objects:
            source = DependencyNode(
                name=self._object_name(sql_object),
                object_type=sql_object.object_type,
            )
            graph.add_node(source)

            for reference in sql_object.references:
                target = DependencyNode(
                    name=self._reference_name(reference),
                    object_type="Unknown",
                )
                graph.add_dependency(source, target, self._dependency_kind(reference))

    @staticmethod
    def _object_name(sql_object: SqlObject) -> str:
        return DependencyResolver._qualified_name(sql_object.name, sql_object.schema)

    @staticmethod
    def _reference_name(reference: Reference) -> str:
        return DependencyResolver._qualified_name(
            reference.name,
            reference.schema,
            reference.database,
        )

    @staticmethod
    def _qualified_name(name: str, schema: str | None = None, database: str | None = None) -> str:
        parts = [part.strip() for part in (database, schema, name) if part and part.strip()]
        if not parts:
            raise ValueError("SQL object name cannot be empty")
        return ".".join(parts)

    @staticmethod
    def _dependency_kind(reference: Reference) -> DependencyKind:
        return DependencyKind.EXECUTES if reference.kind.casefold() == "call" else DependencyKind.REFERENCES
