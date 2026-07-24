from __future__ import annotations

from collections import deque

from .models import ImpactResult


class ImpactAnalysisEngine:
    """Calculates the transitive dependency impact from a SQL object."""

    @staticmethod
    def _name(value: object) -> str:
        name = getattr(value, "name", value)
        return str(name)

    def _dependencies_of(self, graph: object, object_name: str) -> tuple[str, ...]:
        resolver = getattr(graph, "dependencies_of", None)
        if callable(resolver):
            return tuple(self._name(node) for node in resolver(object_name))

        dependencies: list[str] = []
        for edge in getattr(graph, "edges", ()):
            source = self._name(getattr(edge, "source", ""))
            if source.casefold() == object_name.casefold():
                dependencies.append(self._name(getattr(edge, "target", "")))
        return tuple(sorted(set(dependencies), key=str.casefold))

    def analyze(self, graph: object, root_object: str) -> ImpactResult:
        normalized_root = root_object.strip()
        if not normalized_root:
            raise ValueError("root_object must be a non-empty string")

        impacted: list[str] = []
        visited: set[str] = set()
        queue = deque([normalized_root])

        while queue:
            current = queue.popleft()
            key = current.casefold()
            if key in visited:
                continue

            visited.add(key)
            impacted.append(current)
            queue.extend(self._dependencies_of(graph, current))

        return ImpactResult(
            root_object=normalized_root,
            impacted_objects=impacted,
        )
