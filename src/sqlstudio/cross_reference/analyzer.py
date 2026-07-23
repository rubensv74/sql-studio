from __future__ import annotations

from collections.abc import Iterable

from sqlstudio.dependencies import DependencyAnalyzer

from .engine import CrossReferenceEngine
from .models import CrossReference


class CrossReferenceAnalyzer:
    """Facade that parses SQL text and returns cross-references."""

    def __init__(
        self,
        dependency_analyzer: DependencyAnalyzer | None = None,
        engine: CrossReferenceEngine | None = None,
    ) -> None:
        self._dependency_analyzer = dependency_analyzer or DependencyAnalyzer()
        self._engine = engine or CrossReferenceEngine()

    def analyze(self, sql_text: str) -> tuple[CrossReference, ...]:
        """Parse one SQL script and return all direct cross-references."""

        graph = self._dependency_analyzer.analyze(sql_text)
        return self._engine.build(graph)

    def analyze_many(
        self,
        sql_texts: Iterable[str],
    ) -> tuple[CrossReference, ...]:
        """Parse multiple SQL scripts and return merged cross-references."""

        graph = self._dependency_analyzer.analyze_many(sql_texts)
        return self._engine.build(graph)

    def outgoing(
        self,
        sql_texts: str | Iterable[str],
        object_name: str,
    ) -> tuple[CrossReference, ...]:
        """Return references originating from ``object_name``."""

        graph = self._build_graph(sql_texts)
        return self._engine.outgoing(graph, object_name)

    def incoming(
        self,
        sql_texts: str | Iterable[str],
        object_name: str,
    ) -> tuple[CrossReference, ...]:
        """Return references targeting ``object_name``."""

        graph = self._build_graph(sql_texts)
        return self._engine.incoming(graph, object_name)

    def _build_graph(self, sql_texts: str | Iterable[str]):
        if isinstance(sql_texts, str):
            return self._dependency_analyzer.analyze(sql_texts)
        return self._dependency_analyzer.analyze_many(sql_texts)
