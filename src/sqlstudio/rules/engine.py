from __future__ import annotations

from collections.abc import Iterable

from .base import StaticAnalysisRule
from .builtin import CircularDependencyRule, DeadObjectCandidateRule
from .models import RuleContext, StaticAnalysisResult


class StaticAnalysisRuleEngine:
    """Execute normalized rules against one shared parsed dependency context."""

    def __init__(self, rules: Iterable[StaticAnalysisRule] | None = None) -> None:
        configured = tuple(rules) if rules is not None else (
            CircularDependencyRule(),
            DeadObjectCandidateRule(),
        )
        if not configured:
            raise ValueError("StaticAnalysisRuleEngine requires at least one rule")

        by_id: dict[str, StaticAnalysisRule] = {}
        for rule in configured:
            rule_id = self._normalize_rule_id(rule.rule_id)
            if rule_id in by_id:
                raise ValueError(f"Duplicate static-analysis rule id: {rule_id}")
            by_id[rule_id] = rule
        self._rules_by_id = by_id

    @staticmethod
    def _normalize_rule_id(rule_id: str) -> str:
        normalized = rule_id.strip().upper()
        if not normalized:
            raise ValueError("Static-analysis rule id cannot be empty")
        return normalized

    @property
    def rule_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._rules_by_id))

    def run(
        self,
        context: RuleContext,
        *,
        rule_ids: Iterable[str] = (),
    ) -> StaticAnalysisResult:
        requested = tuple(rule_ids)
        if requested:
            normalized_ids = tuple(
                dict.fromkeys(self._normalize_rule_id(rule_id) for rule_id in requested)
            )
            unknown = tuple(rule_id for rule_id in normalized_ids if rule_id not in self._rules_by_id)
            if unknown:
                available = ", ".join(self.rule_ids)
                raise ValueError(
                    f"Unknown static-analysis rule(s): {', '.join(unknown)}. "
                    f"Available rules: {available}"
                )
        else:
            normalized_ids = self.rule_ids

        rule_results = tuple(
            self._rules_by_id[rule_id].evaluate(context)
            for rule_id in normalized_ids
        )
        return StaticAnalysisResult(
            rule_results=rule_results,
            graph_node_count=len(context.graph.nodes),
            dependency_edge_count=len(context.graph.edges),
            parsed_object_count=context.parsed_object_count,
            dynamic_sql_object_count=context.dynamic_sql_object_count,
            entry_points=context.entry_points,
        )
