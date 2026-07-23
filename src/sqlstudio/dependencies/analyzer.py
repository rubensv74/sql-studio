from __future__ import annotations

from collections.abc import Iterable

from sqlstudio.parser import SQLParser

from .graph import DependencyGraph
from .resolver import DependencyResolver


class DependencyAnalyzer:
    """Facade that parses SQL text and returns its dependency graph."""

    def __init__(
        self,
        parser: SQLParser | None = None,
        resolver: DependencyResolver | None = None,
    ) -> None:
        self._parser = parser or SQLParser()
        self._resolver = resolver or DependencyResolver()

    def analyze(self, sql_text: str) -> DependencyGraph:
        """Parse one SQL script and resolve its direct dependencies."""

        document = self._parser.parse(sql_text)
        return self._resolver.resolve(document)

    def analyze_many(self, sql_texts: Iterable[str]) -> DependencyGraph:
        """Parse multiple SQL scripts and merge them into one graph."""

        documents = [self._parser.parse(sql_text) for sql_text in sql_texts]
        return self._resolver.resolve(documents)
