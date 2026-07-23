from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from .models import DependencyEdge, DependencyKind, DependencyNode


class DependencyGraph:
    """In-memory directed graph for SQL object dependencies."""

    def __init__(self) -> None:
        self._nodes: dict[str, DependencyNode] = {}
        self._edges: set[DependencyEdge] = set()
        self._outgoing: dict[str, set[DependencyEdge]] = defaultdict(set)
        self._incoming: dict[str, set[DependencyEdge]] = defaultdict(set)

    @staticmethod
    def _key(name: str) -> str:
        normalized = name.strip()
        if not normalized:
            raise ValueError("Dependency node name cannot be empty")
        return normalized.casefold()

    def add_node(self, node: DependencyNode) -> DependencyNode:
        """Add a node or return the existing node with the same normalized name."""

        key = self._key(node.name)
        existing = self._nodes.get(key)
        if existing is not None:
            return existing
        self._nodes[key] = node
        return node

    def get_node(self, name: str) -> DependencyNode | None:
        return self._nodes.get(self._key(name))

    def add_dependency(
        self,
        source: DependencyNode,
        target: DependencyNode,
        kind: DependencyKind = DependencyKind.REFERENCES,
    ) -> DependencyEdge:
        """Create a directed edge and ensure both endpoint nodes exist."""

        source_node = self.add_node(source)
        target_node = self.add_node(target)
        edge = DependencyEdge(source=source_node, target=target_node, kind=kind)
        if edge not in self._edges:
            self._edges.add(edge)
            self._outgoing[self._key(source_node.name)].add(edge)
            self._incoming[self._key(target_node.name)].add(edge)
        return edge

    def dependencies_of(self, name: str) -> tuple[DependencyNode, ...]:
        """Return direct targets referenced or executed by the named object."""

        edges = self._outgoing.get(self._key(name), set())
        return tuple(sorted((edge.target for edge in edges), key=lambda node: node.name.casefold()))

    def dependents_of(self, name: str) -> tuple[DependencyNode, ...]:
        """Return direct source objects that depend on the named object."""

        edges = self._incoming.get(self._key(name), set())
        return tuple(sorted((edge.source for edge in edges), key=lambda node: node.name.casefold()))

    @property
    def nodes(self) -> tuple[DependencyNode, ...]:
        return tuple(sorted(self._nodes.values(), key=lambda node: node.name.casefold()))

    @property
    def edges(self) -> tuple[DependencyEdge, ...]:
        return tuple(
            sorted(
                self._edges,
                key=lambda edge: (
                    edge.source.name.casefold(),
                    edge.target.name.casefold(),
                    edge.kind.value,
                ),
            )
        )

    def extend(self, edges: Iterable[DependencyEdge]) -> None:
        for edge in edges:
            self.add_dependency(edge.source, edge.target, edge.kind)
