from __future__ import annotations

from typing import Protocol

from .models import RuleContext, RuleResult, Severity


class StaticAnalysisRule(Protocol):
    """Protocol implemented by every consolidated static-analysis rule."""

    rule_id: str
    title: str
    description: str
    default_severity: Severity

    def evaluate(self, context: RuleContext) -> RuleResult:
        """Evaluate one shared analysis context and return normalized findings."""
        ...
