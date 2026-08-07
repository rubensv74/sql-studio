from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TypeAlias

from sqlstudio.dependencies import DependencyGraph
from sqlstudio.parser import SqlDocument

RulePropertyValue: TypeAlias = str | int | bool


class Severity(str, Enum):
    """Stable severity levels used by static-analysis rules."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

    @property
    def rank(self) -> int:
        return {
            Severity.INFO: 10,
            Severity.WARNING: 20,
            Severity.ERROR: 30,
        }[self]

    @classmethod
    def parse(cls, value: str | Severity) -> Severity:
        if isinstance(value, cls):
            return value
        normalized = value.strip().casefold()
        try:
            return cls(normalized)
        except ValueError as exc:
            allowed = ", ".join(item.value for item in cls)
            raise ValueError(f"Unsupported severity '{value}'. Expected one of: {allowed}") from exc


@dataclass(frozen=True)
class Finding:
    """One normalized, actionable finding emitted by a static-analysis rule."""

    rule_id: str
    severity: Severity
    title: str
    message: str
    objects: tuple[str, ...] = field(default_factory=tuple)
    properties: tuple[tuple[str, RulePropertyValue], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        rule_id = self.rule_id.strip().upper()
        title = self.title.strip()
        message = self.message.strip()
        if not rule_id:
            raise ValueError("Finding rule_id cannot be empty")
        if not title:
            raise ValueError("Finding title cannot be empty")
        if not message:
            raise ValueError("Finding message cannot be empty")

        canonical_objects: dict[str, str] = {}
        for raw_name in self.objects:
            name = raw_name.strip()
            if name:
                canonical_objects.setdefault(name.casefold(), name)
        normalized_objects = tuple(sorted(canonical_objects.values(), key=str.casefold))

        normalized_property_map: dict[str, tuple[str, RulePropertyValue]] = {}
        for raw_key, value in self.properties:
            key = raw_key.strip()
            if not key:
                raise ValueError("Finding property key cannot be empty")
            folded = key.casefold()
            if folded in normalized_property_map:
                raise ValueError("Finding property keys must be unique")
            normalized_property_map[folded] = (key, value)
        normalized_properties = tuple(
            sorted(normalized_property_map.values(), key=lambda item: item[0].casefold())
        )

        object.__setattr__(self, "rule_id", rule_id)
        object.__setattr__(self, "severity", Severity.parse(self.severity))
        object.__setattr__(self, "title", title)
        object.__setattr__(self, "message", message)
        object.__setattr__(self, "objects", normalized_objects)
        object.__setattr__(self, "properties", normalized_properties)


@dataclass(frozen=True)
class RuleResult:
    """Execution result for one static-analysis rule."""

    rule_id: str
    title: str
    default_severity: Severity
    findings: tuple[Finding, ...] = field(default_factory=tuple)
    properties: tuple[tuple[str, RulePropertyValue], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        rule_id = self.rule_id.strip().upper()
        title = self.title.strip()
        if not rule_id:
            raise ValueError("RuleResult rule_id cannot be empty")
        if not title:
            raise ValueError("RuleResult title cannot be empty")
        if any(finding.rule_id != rule_id for finding in self.findings):
            raise ValueError("All findings in a RuleResult must match its rule_id")

        property_map: dict[str, tuple[str, RulePropertyValue]] = {}
        for raw_key, value in self.properties:
            key = raw_key.strip()
            if not key:
                raise ValueError("RuleResult property key cannot be empty")
            folded = key.casefold()
            if folded in property_map:
                raise ValueError("RuleResult property keys must be unique")
            property_map[folded] = (key, value)

        object.__setattr__(self, "rule_id", rule_id)
        object.__setattr__(self, "title", title)
        object.__setattr__(self, "default_severity", Severity.parse(self.default_severity))
        object.__setattr__(
            self,
            "findings",
            tuple(
                sorted(
                    self.findings,
                    key=lambda finding: (
                        finding.rule_id,
                        tuple(name.casefold() for name in finding.objects),
                        finding.message.casefold(),
                    ),
                )
            ),
        )
        object.__setattr__(
            self,
            "properties",
            tuple(sorted(property_map.values(), key=lambda item: item[0].casefold())),
        )


@dataclass(frozen=True)
class RuleContext:
    """Shared parsed state supplied to every rule in one analysis run."""

    documents: tuple[SqlDocument, ...]
    graph: DependencyGraph
    entry_points: tuple[str, ...] = field(default_factory=tuple)

    @property
    def dynamic_sql_object_count(self) -> int:
        return sum(
            1
            for document in self.documents
            for sql_object in document.objects
            if sql_object.dynamic_sql
        )

    @property
    def parsed_object_count(self) -> int:
        return sum(len(document.objects) for document in self.documents)


@dataclass(frozen=True)
class StaticAnalysisResult:
    """Consolidated result from one execution of the static-analysis rule engine."""

    rule_results: tuple[RuleResult, ...]
    graph_node_count: int
    dependency_edge_count: int
    parsed_object_count: int
    dynamic_sql_object_count: int
    entry_points: tuple[str, ...] = field(default_factory=tuple)

    @property
    def findings(self) -> tuple[Finding, ...]:
        return tuple(
            finding
            for rule_result in self.rule_results
            for finding in rule_result.findings
        )

    def count(self, severity: Severity | str) -> int:
        level = Severity.parse(severity)
        return sum(1 for finding in self.findings if finding.severity is level)

    def has_at_or_above(self, severity: Severity | str) -> bool:
        threshold = Severity.parse(severity).rank
        return any(finding.severity.rank >= threshold for finding in self.findings)
