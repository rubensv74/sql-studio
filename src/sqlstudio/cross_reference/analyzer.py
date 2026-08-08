from __future__ import annotations

from collections.abc import Iterable

from sqlstudio.dependencies import DependencyAnalyzer
from sqlstudio.source import SqlSource

from .engine import CrossReferenceEngine
from .models import CrossReference


class CrossReferenceAnalyzer:
    """Facade that builds direct cross-references from SQL inputs."""

    def __init__(
        self,
        dependency_analyzer: DependencyAnalyzer | None = None,
        engine: CrossReferenceEngine | None = None,
    ) -> None:
        self._dependency_analyzer = dependency_analyzer or DependencyAnalyzer()
        self._engine = engine or CrossReferenceEngine()

    def analyze(self, sql_text: str) -> tuple[CrossReference, ...]:
        graph = self._dependency_analyzer.analyze(sql_text)
        return self._engine.build(graph)

    def analyze_many(self, sql_texts: Iterable[str]) -> tuple[CrossReference, ...]:
        graph = self._dependency_analyzer.analyze_many(sql_texts)
        return self._engine.build(graph)

    def analyze_source(self, source: SqlSource) -> tuple[CrossReference, ...]:
        graph = self._dependency_analyzer.analyze_source(source)
        return self._engine.build(graph)

    def analyze_sources(self, sources: Iterable[SqlSource]) -> tuple[CrossReference, ...]:
        graph = self._dependency_analyzer.analyze_sources(sources)
        return self._engine.build(graph)

    def outgoing(
        self,
        sql_texts: str | Iterable[str],
        object_name: str,
    ) -> tuple[CrossReference, ...]:
        graph = self._build_graph(sql_texts)
        return self._engine.outgoing(graph, object_name)

    def incoming(
        self,
        sql_texts: str | Iterable[str],
        object_name: str,
    ) -> tuple[CrossReference, ...]:
        graph = self._build_graph(sql_texts)
        return self._engine.incoming(graph, object_name)

    def outgoing_sources(
        self,
        sources: Iterable[SqlSource],
        object_name: str,
    ) -> tuple[CrossReference, ...]:
        graph = self._dependency_analyzer.analyze_sources(sources)
        return self._engine.outgoing(graph, object_name)

    def incoming_sources(
        self,
        sources: Iterable[SqlSource],
        object_name: str,
    ) -> tuple[CrossReference, ...]:
        graph = self._dependency_analyzer.analyze_sources(sources)
        return self._engine.incoming(graph, object_name)

    def _build_graph(self, sql_texts: str | Iterable[str]):
        if isinstance(sql_texts, str):
            return self._dependency_analyzer.analyze(sql_texts)
        return self._dependency_analyzer.analyze_many(sql_texts)
