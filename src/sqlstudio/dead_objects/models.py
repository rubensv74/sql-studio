from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, order=True)
class DeadObjectMember:
    """One locally defined SQL object participating in a dead-object finding."""

    name: str
    object_type: str


@dataclass(frozen=True)
class DeadObjectFinding:
    """One candidate dead component in the analyzed static dependency graph."""

    members: tuple[DeadObjectMember, ...]
    is_circular_component: bool = False
    reason: str = "no_incoming_static_references_from_outside_component"
    external_usage_possible: bool = True


@dataclass(frozen=True, order=True)
class DeadObjectExclusion:
    """A candidate root excluded by an explicit or implicit entry-point rule."""

    name: str
    object_type: str
    reason: str


@dataclass(frozen=True)
class DeadObjectResult:
    """Static dead-object candidate analysis result."""

    findings: tuple[DeadObjectFinding, ...] = field(default_factory=tuple)
    excluded_objects: tuple[DeadObjectExclusion, ...] = field(default_factory=tuple)
    defined_object_count: int = 0
    entry_points: tuple[str, ...] = field(default_factory=tuple)
    dynamic_sql_object_count: int = 0
