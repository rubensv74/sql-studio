from __future__ import annotations

from dataclasses import dataclass, field

from sqlstudio.circular_dependencies import CircularDependency
from sqlstudio.dead_objects import DeadObjectResult
from sqlstudio.dependencies import DependencyGraph
from sqlstudio.rules import StaticAnalysisResult


_DURABLE_TYPES = frozenset({"stored procedure", "view", "function", "trigger", "table"})


@dataclass(frozen=True)
class RepositorySourceRecord:
    """Physical SQL source and the locally defined objects parsed from it."""

    source_id: str
    path: str | None = None
    objects: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RepositoryObjectRecord:
    """One locally defined SQL object enriched with graph relationships."""

    name: str
    object_type: str
    source_id: str
    dynamic_sql: bool = False
    dependencies: tuple[str, ...] = field(default_factory=tuple)
    dependents: tuple[str, ...] = field(default_factory=tuple)

    @property
    def dependency_count(self) -> int:
        return len(self.dependencies)

    @property
    def dependent_count(self) -> int:
        return len(self.dependents)

    @property
    def is_script(self) -> bool:
        return self.object_type.strip().casefold() == "script"

    @property
    def is_durable(self) -> bool:
        return self.object_type.strip().casefold() in _DURABLE_TYPES


@dataclass(frozen=True)
class RepositoryAnalysisResult:
    """Canonical product-level result for one repository analysis run."""

    sources: tuple[RepositorySourceRecord, ...]
    objects: tuple[RepositoryObjectRecord, ...]
    graph: DependencyGraph
    cycles: tuple[CircularDependency, ...]
    dead_objects: DeadObjectResult
    static_analysis: StaticAnalysisResult
    entry_points: tuple[str, ...] = field(default_factory=tuple)

    @property
    def source_count(self) -> int:
        return len(self.sources)

    @property
    def parsed_object_count(self) -> int:
        return len(self.objects)

    @property
    def durable_object_count(self) -> int:
        return sum(1 for item in self.objects if item.is_durable)

    @property
    def script_object_count(self) -> int:
        return sum(1 for item in self.objects if item.is_script)

    @property
    def dynamic_sql_objects(self) -> tuple[RepositoryObjectRecord, ...]:
        return tuple(item for item in self.objects if item.dynamic_sql)

    @property
    def key_objects(self) -> tuple[RepositoryObjectRecord, ...]:
        """Return locally defined objects ranked by incoming dependent count."""

        return tuple(
            sorted(
                self.objects,
                key=lambda item: (-item.dependent_count, item.name.casefold()),
            )
        )
