from __future__ import annotations

from dataclasses import dataclass

from sqlstudio.dependencies import DependencyEdge


@dataclass(frozen=True)
class CircularDependency:
    """One strongly connected component that contains a dependency cycle."""

    members: tuple[str, ...]
    edges: tuple[DependencyEdge, ...]

    @property
    def is_self_reference(self) -> bool:
        """Return whether the circular dependency is a single self-referencing object."""

        return len(self.members) == 1
