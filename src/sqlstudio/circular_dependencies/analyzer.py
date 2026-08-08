from __future__ import annotations

from collections.abc import Iterable

from sqlstudio.dependencies import DependencyAnalyzer
from sqlstudio.source import SqlSource

from .engine import CircularDependencyEngine
from .models import CircularDependency


class CircularDependencyAnalyzer:
    """Facade that builds a dependency graph and detects circular components."""

    def __init__(
        self,
        dependency_analyzer: DependencyAnalyzer | None = None,
        engine: CircularDependencyEngine | None = None,
    ) -> None:
        self._dependency_analyzer = dependency_analyzer or DependencyAnalyzer()
        self._engine = engine or CircularDependencyEngine()

    def analyze(self, sql_text: str) -> tuple[CircularDependency, ...]:
        graph = self._dependency_analyzer.analyze(sql_text)
        return self._engine.detect(graph)

    def analyze_many(self, sql_texts: Iterable[str]) -> tuple[CircularDependency, ...]:
        graph = self._dependency_analyzer.analyze_many(sql_texts)
        return self._engine.detect(graph)

    def analyze_source(self, source: SqlSource) -> tuple[CircularDependency, ...]:
        graph = self._dependency_analyzer.analyze_source(source)
        return self._engine.detect(graph)

    def analyze_sources(self, sources: Iterable[SqlSource]) -> tuple[CircularDependency, ...]:
        graph = self._dependency_analyzer.analyze_sources(sources)
        return self._engine.detect(graph)
