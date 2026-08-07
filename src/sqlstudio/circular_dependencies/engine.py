from __future__ import annotations

from sqlstudio.dependencies import DependencyGraph

from .models import CircularDependency


class CircularDependencyEngine:
    """Detect circular SQL dependencies as strongly connected components."""

    @staticmethod
    def _key(name: str) -> str:
        return name.strip().casefold()

    def detect(self, graph: DependencyGraph) -> tuple[CircularDependency, ...]:
        """Return deterministic circular components from ``graph``.

        Components with more than one object are circular by definition. A
        single-object component is returned only when the object has a
        self-referencing dependency edge.
        """

        nodes_by_key = {self._key(node.name): node for node in graph.nodes}
        adjacency = {
            key: tuple(
                self._key(target.name)
                for target in graph.dependencies_of(node.name)
            )
            for key, node in nodes_by_key.items()
        }

        index = 0
        indices: dict[str, int] = {}
        lowlinks: dict[str, int] = {}
        stack: list[str] = []
        on_stack: set[str] = set()
        components: list[set[str]] = []

        def strong_connect(node_key: str) -> None:
            nonlocal index
            indices[node_key] = index
            lowlinks[node_key] = index
            index += 1
            stack.append(node_key)
            on_stack.add(node_key)

            for target_key in adjacency.get(node_key, ()):
                if target_key not in indices:
                    strong_connect(target_key)
                    lowlinks[node_key] = min(
                        lowlinks[node_key],
                        lowlinks[target_key],
                    )
                elif target_key in on_stack:
                    lowlinks[node_key] = min(
                        lowlinks[node_key],
                        indices[target_key],
                    )

            if lowlinks[node_key] != indices[node_key]:
                return

            component: set[str] = set()
            while True:
                member_key = stack.pop()
                on_stack.remove(member_key)
                component.add(member_key)
                if member_key == node_key:
                    break
            components.append(component)

        for node_key in sorted(nodes_by_key):
            if node_key not in indices:
                strong_connect(node_key)

        cycles: list[CircularDependency] = []
        for component in components:
            internal_edges = tuple(
                edge
                for edge in graph.edges
                if self._key(edge.source.name) in component
                and self._key(edge.target.name) in component
            )
            has_self_reference = any(
                self._key(edge.source.name) == self._key(edge.target.name)
                for edge in internal_edges
            )
            if len(component) == 1 and not has_self_reference:
                continue

            members = tuple(
                sorted(
                    (nodes_by_key[key].name for key in component),
                    key=str.casefold,
                )
            )
            cycles.append(
                CircularDependency(
                    members=members,
                    edges=internal_edges,
                )
            )

        return tuple(
            sorted(
                cycles,
                key=lambda cycle: tuple(member.casefold() for member in cycle.members),
            )
        )
