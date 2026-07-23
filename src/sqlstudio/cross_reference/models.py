from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CrossReferenceType(str, Enum):
    """Supported cross-reference relationships between SQL objects."""

    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    CREATE = "create"
    ALTER = "alter"
    DROP = "drop"


@dataclass(frozen=True, order=True)
class CrossReference:
    """Directed cross-reference from one SQL object to another."""

    source: str
    target: str
    reference_type: CrossReferenceType

    def __post_init__(self) -> None:
        source = self.source.strip()
        target = self.target.strip()
        if not source:
            raise ValueError("Cross-reference source cannot be empty")
        if not target:
            raise ValueError("Cross-reference target cannot be empty")
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "target", target)
