from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DependencyKind(str, Enum):
    """Supported SQL dependency relationships."""

    REFERENCES = "references"
    EXECUTES = "executes"


@dataclass(frozen=True, order=True)
class DependencyNode:
    """Identifies one SQL object in the dependency graph."""

    name: str
    object_type: str = "Unknown"

    def __post_init__(self) -> None:
        normalized_name = self.name.strip()
        normalized_type = self.object_type.strip() or "Unknown"
        if not normalized_name:
            raise ValueError("Dependency node name cannot be empty")
        object.__setattr__(self, "name", normalized_name)
        object.__setattr__(self, "object_type", normalized_type)


@dataclass(frozen=True, order=True)
class DependencyEdge:
    """Directed relationship from one SQL object to another."""

    source: DependencyNode
    target: DependencyNode
    kind: DependencyKind = DependencyKind.REFERENCES
