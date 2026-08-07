from __future__ import annotations

from collections.abc import Iterable

from sqlstudio.dependencies import DependencyResolver
from sqlstudio.parser import SQLParser

from .engine import StaticAnalysisRuleEngine
from .models import RuleContext, StaticAnalysisResult


class StaticAnalysisAnalyzer:
    """Parse SQL once, build one graph, then execute the configured rule set."""

    def __init__(
        self,
        parser: SQLParser | None = None,
        resolver: DependencyResolver | None = None,
        engine: StaticAnalysisRuleEngine | None = None,
    ) -> None:
        self._parser = parser or SQLParser()
        self._resolver = resolver or DependencyResolver()
        self._engine = engine or StaticAnalysisRuleEngine()

    @staticmethod
    def _normalize_entry_points(entry_points: Iterable[str]) -> tuple[str, ...]:
        canonical: dict[str, str] = {}
        for raw in entry_points:
            name = raw.strip()
            if not name:
                raise ValueError("Entry point name cannot be empty")
            canonical.setdefault(name.casefold(), name)
        return tuple(sorted(canonical.values(), key=str.casefold))

    def analyze(
        self,
        sql_text: str,
        *,
        entry_points: Iterable[str] = (),
        rule_ids: Iterable[str] = (),
    ) -> StaticAnalysisResult:
        return self.analyze_many(
            [sql_text],
            entry_points=entry_points,
            rule_ids=rule_ids,
        )

    def analyze_many(
        self,
        sql_texts: Iterable[str],
        *,
        entry_points: Iterable[str] = (),
        rule_ids: Iterable[str] = (),
    ) -> StaticAnalysisResult:
        documents = tuple(self._parser.parse(sql_text) for sql_text in sql_texts)
        graph = self._resolver.resolve(documents)
        context = RuleContext(
            documents=documents,
            graph=graph,
            entry_points=self._normalize_entry_points(entry_points),
        )
        return self._engine.run(context, rule_ids=rule_ids)
