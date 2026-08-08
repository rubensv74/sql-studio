from __future__ import annotations

from collections.abc import Iterable

from sqlstudio.dependencies import DependencyAnalyzer
from sqlstudio.source import SqlSource

from .engine import ImpactAnalysisEngine


class ImpactAnalyzer:
    def __init__(self) -> None:
        self._dependency = DependencyAnalyzer()
        self._engine = ImpactAnalysisEngine()

    def analyze(self, sql_text: str, root_object: str):
        graph = self._dependency.analyze(sql_text)
        return self._engine.analyze(graph, root_object)

    def analyze_many(self, sql_texts: Iterable[str], root_object: str):
        graph = self._dependency.analyze_many(sql_texts)
        return self._engine.analyze(graph, root_object)

    def analyze_source(self, source: SqlSource, root_object: str):
        graph = self._dependency.analyze_source(source)
        return self._engine.analyze(graph, root_object)

    def analyze_sources(self, sources: Iterable[SqlSource], root_object: str):
        graph = self._dependency.analyze_sources(sources)
        return self._engine.analyze(graph, root_object)
