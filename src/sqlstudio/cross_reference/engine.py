from __future__ import annotations

from collections.abc import Iterable

from sqlstudio.dependencies import DependencyGraph, DependencyKind

from .models import CrossReference, CrossReferenceType


class CrossReferenceEngine:
    """Build and query cross-references derived from a dependency graph."""

    _TYPE_BY_DEPENDENCY_KIND = {
        DependencyKind.REFERENCES: CrossReferenceType.READ,
        DependencyKind.EXECUTES: CrossReferenceType.EXECUTE,
    }

    def build(self, graph: DependencyGraph) -> tuple[CrossReference, ...]:
        """Return deterministic cross-references for every dependency edge."""

        references = {
            CrossReference(
                source=edge.source.name,
                target=edge.target.name,
                reference_type=self._TYPE_BY_DEPENDENCY_KIND[edge.kind],
            )
            for edge in graph.edges
        }
        return self._sorted(references)

    def outgoing(
        self,
        graph: DependencyGraph,
        object_name: str,
    ) -> tuple[CrossReference, ...]:
        """Return references originating from ``object_name``."""

        key = self._normalized_key(object_name)
        return tuple(
            reference
            for reference in self.build(graph)
            if reference.source.casefold() == key
        )

    def incoming(
        self,
        graph: DependencyGraph,
        object_name: str,
    ) -> tuple[CrossReference, ...]:
        """Return references targeting ``object_name``."""

        key = self._normalized_key(object_name)
        return tuple(
            reference
            for reference in self.build(graph)
            if reference.target.casefold() == key
        )

    @staticmethod
    def _normalized_key(object_name: str) -> str:
        normalized = object_name.strip()
        if not normalized:
            raise ValueError("SQL object name cannot be empty")
        return normalized.casefold()

    @staticmethod
    def _sorted(
        references: Iterable[CrossReference],
    ) -> tuple[CrossReference, ...]:
        return tuple(
            sorted(
                references,
                key=lambda reference: (
                    reference.source.casefold(),
                    reference.target.casefold(),
                    reference.reference_type.value,
                ),
            )
        )
