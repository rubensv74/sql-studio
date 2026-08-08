from __future__ import annotations

from collections.abc import Iterable

from sqlstudio.parser import SQLParser
from sqlstudio.source import SqlSource

from .graph import DependencyGraph
from .resolver import DependencyResolver


class DependencyAnalyzer:
    """Facade that parses SQL inputs and returns their dependency graph."""

    def __init__(
        self,
        parser: SQLParser | None = None,
        resolver: DependencyResolver | None = None,
    ) -> None:
        self._parser = parser or SQLParser()
        self._resolver = resolver or DependencyResolver()

    def analyze(self, sql_text: str) -> DependencyGraph:
        """Parse one raw SQL string using the compatibility contract."""

        document = self._parser.parse(sql_text)
        return self._resolver.resolve(document)

    def analyze_many(self, sql_texts: Iterable[str]) -> DependencyGraph:
        """Parse raw SQL strings using the compatibility contract."""

        documents = [self._parser.parse(sql_text) for sql_text in sql_texts]
        return self._resolver.resolve(documents)

    def analyze_source(self, source: SqlSource) -> DependencyGraph:
        """Parse one physical SQL source with stable script identity."""

        return self._resolver.resolve(self._parser.parse_source(source))

    def analyze_sources(self, sources: Iterable[SqlSource]) -> DependencyGraph:
        """Parse physical SQL sources and merge them without script collisions."""

        documents = [self._parser.parse_source(source) for source in sources]
        return self._resolver.resolve(documents)
