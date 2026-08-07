from __future__ import annotations

from collections.abc import Iterable

from sqlstudio.circular_dependencies import CircularDependencyEngine
from sqlstudio.dependencies import DependencyGraph

from .models import (
    DeadObjectExclusion,
    DeadObjectFinding,
    DeadObjectMember,
    DeadObjectResult,
)


class DeadObjectEngine:
    """Identify conservative dead-object candidates from a dependency graph.

    The engine never claims that an object is safe to delete. It reports locally
    defined components with no incoming static references from outside the
    component. Such roots may still be invoked externally, so every finding is
    explicitly a review candidate.
    """

    IMPLICIT_ENTRY_OBJECT_TYPES = frozenset({"trigger"})

    def __init__(
        self,
        circular_engine: CircularDependencyEngine | None = None,
    ) -> None:
        self._circular_engine = circular_engine or CircularDependencyEngine()

    @staticmethod
    def _key(name: str) -> str:
        normalized = name.strip()
        if not normalized:
            raise ValueError("SQL object name cannot be empty")
        return normalized.casefold()

    @staticmethod
    def _is_defined(object_type: str) -> bool:
        return object_type.strip().casefold() != "unknown"

    def detect(
        self,
        graph: DependencyGraph,
        *,
        entry_points: Iterable[str] = (),
    ) -> DeadObjectResult:
        """Return deterministic dead-object candidates and explicit exclusions."""

        defined_by_key = {
            self._key(node.name): node
            for node in graph.nodes
            if self._is_defined(node.object_type)
        }

        declared_entry_keys: set[str] = set()
        for entry_point in entry_points:
            key = self._key(entry_point)
            if key not in defined_by_key:
                raise ValueError(
                    f"Declared entry point is not a defined SQL object: {entry_point}"
                )
            declared_entry_keys.add(key)

        canonical_entry_points = tuple(
            sorted(
                (defined_by_key[key].name for key in declared_entry_keys),
                key=str.casefold,
            )
        )

        circular_components = {
            frozenset(self._key(member) for member in cycle.members)
            for cycle in self._circular_engine.detect(graph)
        }
        component_by_key: dict[str, frozenset[str]] = {}
        for component in circular_components:
            for key in component:
                component_by_key[key] = component

        findings: list[DeadObjectFinding] = []
        exclusions: list[DeadObjectExclusion] = []
        processed: set[str] = set()

        for key in sorted(defined_by_key):
            if key in processed:
                continue

            component = component_by_key.get(key, frozenset({key}))
            component = frozenset(
                member_key
                for member_key in component
                if member_key in defined_by_key
            )
            processed.update(component)

            has_external_incoming = any(
                self._key(edge.target.name) in component
                and self._key(edge.source.name) not in component
                for edge in graph.edges
            )
            if has_external_incoming:
                continue

            member_nodes = tuple(
                sorted(
                    (defined_by_key[member_key] for member_key in component),
                    key=lambda node: node.name.casefold(),
                )
            )

            contains_declared_entry = any(
                member_key in declared_entry_keys for member_key in component
            )
            contains_implicit_entry = any(
                node.object_type.casefold() in self.IMPLICIT_ENTRY_OBJECT_TYPES
                for node in member_nodes
            )

            exclusion_reason: str | None = None
            if contains_declared_entry:
                exclusion_reason = "component_contains_declared_entry_point"
            elif contains_implicit_entry:
                exclusion_reason = "component_contains_implicit_entry_object"

            if exclusion_reason is not None:
                exclusions.extend(
                    DeadObjectExclusion(
                        name=node.name,
                        object_type=node.object_type,
                        reason=exclusion_reason,
                    )
                    for node in member_nodes
                )
                continue

            findings.append(
                DeadObjectFinding(
                    members=tuple(
                        DeadObjectMember(
                            name=node.name,
                            object_type=node.object_type,
                        )
                        for node in member_nodes
                    ),
                    is_circular_component=component in circular_components,
                )
            )

        return DeadObjectResult(
            findings=tuple(
                sorted(
                    findings,
                    key=lambda finding: tuple(
                        member.name.casefold() for member in finding.members
                    ),
                )
            ),
            excluded_objects=tuple(
                sorted(
                    exclusions,
                    key=lambda exclusion: exclusion.name.casefold(),
                )
            ),
            defined_object_count=len(defined_by_key),
            entry_points=canonical_entry_points,
        )
