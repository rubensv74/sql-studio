from __future__ import annotations

from sqlstudio.circular_dependencies import CircularDependencyEngine
from sqlstudio.dead_objects import DeadObjectEngine

from .models import Finding, RuleContext, RuleResult, Severity


class CircularDependencyRule:
    rule_id = "SQL001"
    title = "Circular dependency"
    description = "Detect strongly connected SQL dependency components and self-references."
    default_severity = Severity.ERROR

    def __init__(self, engine: CircularDependencyEngine | None = None) -> None:
        self._engine = engine or CircularDependencyEngine()

    def evaluate(self, context: RuleContext) -> RuleResult:
        cycles = self._engine.detect(context.graph)
        findings = tuple(
            Finding(
                rule_id=self.rule_id,
                severity=self.default_severity,
                title=self.title,
                message=(
                    "Self-referencing SQL object detected: " + cycle.members[0]
                    if cycle.is_self_reference
                    else "Circular dependency component detected: " + ", ".join(cycle.members)
                ),
                objects=cycle.members,
                properties=(
                    ("internal_edge_count", len(cycle.edges)),
                    ("is_self_reference", cycle.is_self_reference),
                ),
            )
            for cycle in cycles
        )
        return RuleResult(
            rule_id=self.rule_id,
            title=self.title,
            default_severity=self.default_severity,
            findings=findings,
        )


class DeadObjectCandidateRule:
    rule_id = "SQL002"
    title = "Dead object candidate"
    description = (
        "Identify locally defined root components with no incoming static references; "
        "findings always require human review."
    )
    default_severity = Severity.WARNING

    def __init__(self, engine: DeadObjectEngine | None = None) -> None:
        self._engine = engine or DeadObjectEngine()

    def evaluate(self, context: RuleContext) -> RuleResult:
        result = self._engine.detect(context.graph, entry_points=context.entry_points)
        findings = tuple(
            Finding(
                rule_id=self.rule_id,
                severity=self.default_severity,
                title=self.title,
                message="Unreferenced SQL component requires review: "
                + ", ".join(member.name for member in finding.members),
                objects=tuple(member.name for member in finding.members),
                properties=(
                    ("classification", "candidate_only"),
                    ("external_usage_may_exist", finding.external_usage_possible),
                    ("is_circular_component", finding.is_circular_component),
                    ("reason", finding.reason),
                    ("safe_to_delete", False),
                ),
            )
            for finding in result.findings
        )
        return RuleResult(
            rule_id=self.rule_id,
            title=self.title,
            default_severity=self.default_severity,
            findings=findings,
            properties=(
                ("defined_object_count", result.defined_object_count),
                ("excluded_object_count", len(result.excluded_objects)),
            ),
        )
