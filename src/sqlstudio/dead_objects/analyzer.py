from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace

from sqlstudio.dependencies import DependencyResolver
from sqlstudio.parser import SQLParser

from .engine import DeadObjectEngine
from .models import DeadObjectResult


class DeadObjectAnalyzer:
    """Parse SQL sources and identify conservative dead-object candidates."""

    def __init__(
        self,
        parser: SQLParser | None = None,
        resolver: DependencyResolver | None = None,
        engine: DeadObjectEngine | None = None,
    ) -> None:
        self._parser = parser or SQLParser()
        self._resolver = resolver or DependencyResolver()
        self._engine = engine or DeadObjectEngine()

    def analyze(
        self,
        sql_text: str,
        *,
        entry_points: Iterable[str] = (),
    ) -> DeadObjectResult:
        return self.analyze_many([sql_text], entry_points=entry_points)

    def analyze_many(
        self,
        sql_texts: Iterable[str],
        *,
        entry_points: Iterable[str] = (),
    ) -> DeadObjectResult:
        documents = [self._parser.parse(sql_text) for sql_text in sql_texts]
        graph = self._resolver.resolve(documents)
        result = self._engine.detect(graph, entry_points=entry_points)
        dynamic_sql_object_count = sum(
            1
            for document in documents
            for sql_object in document.objects
            if sql_object.dynamic_sql
        )
        return replace(
            result,
            dynamic_sql_object_count=dynamic_sql_object_count,
        )
