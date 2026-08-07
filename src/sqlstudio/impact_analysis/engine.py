from __future__ import annotations

from collections import deque

from sqlstudio.dependencies import DependencyGraph

from .models import ImpactNode, ImpactResult


class ImpactAnalysisEngine:
    """Calculate objects transitively impacted by a change to a SQL object.

    DependencyGraph edges use the direction ``source -> target``, meaning that
    ``source`` depends on ``target``. Impact analysis therefore follows incoming
    edges through ``dependents_of()`` to answer: "what can be affected if this
    object changes?"
    """

    def analyze(self, graph: DependencyGraph, root_object: str) -> ImpactResult:
        """Return the root and every object that depends on it transitively.

        Object-name matching is case-insensitive. The flat result preserves a
        deterministic breadth-first order, while ``tree`` preserves the
        dependent hierarchy exposed by ``DependencyGraph``.
        """

        root_name = self._resolve_root_name(graph, root_object)
        impacted = self._collect_impacted(graph, root_name)
        tree = self._build_tree(graph, root_name, ancestry=frozenset())
        return ImpactResult(
            root_object=root_name,
            impacted_objects=impacted,
            tree=tree,
        )

    def build_tree(self, graph: DependencyGraph, root_object: str) -> ImpactNode:
        """Build a cycle-safe impact tree rooted at ``root_object``."""

        root_name = self._resolve_root_name(graph, root_object)
        return self._build_tree(graph, root_name, ancestry=frozenset())

    @staticmethod
    def _resolve_root_name(graph: DependencyGraph, root_object: str) -> str:
        normalized = root_object.strip()
        if not normalized:
            raise ValueError("root_object must be a non-empty string")

        node = graph.get_node(normalized)
        return node.name if node is not None else normalized

    @staticmethod
    def _collect_impacted(graph: DependencyGraph, root_name: str) -> list[str]:
        queue = deque([root_name])
        seen: set[str] = set()
        impacted: list[str] = []

        while queue:
            current = queue.popleft()
            key = current.casefold()
            if key in seen:
                continue

            seen.add(key)
            impacted.append(current)
            queue.extend(node.name for node in graph.dependents_of(current))

        return impacted

    def _build_tree(
        self,
        graph: DependencyGraph,
        object_name: str,
        *,
        ancestry: frozenset[str],
    ) -> ImpactNode:
        key = object_name.casefold()
        if key in ancestry:
            return ImpactNode(name=object_name)

        next_ancestry = ancestry | {key}
        children = [
            self._build_tree(
                graph,
                dependent.name,
                ancestry=next_ancestry,
            )
            for dependent in graph.dependents_of(object_name)
            if dependent.name.casefold() not in next_ancestry
        ]
        return ImpactNode(name=object_name, children=children)
