from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace

from sqlstudio.circular_dependencies import CircularDependencyEngine
from sqlstudio.dead_objects import DeadObjectEngine
from sqlstudio.dependencies import DependencyResolver
from sqlstudio.parser import SQLParser
from sqlstudio.rules import RuleContext, StaticAnalysisRuleEngine
from sqlstudio.source import SqlSource

from .models import (
    RepositoryAnalysisResult,
    RepositoryObjectRecord,
    RepositorySourceRecord,
)


class RepositoryAnalysisEngine:
    """Build one reusable repository analysis result from physical SQL sources."""

    def __init__(
        self,
        parser: SQLParser | None = None,
        resolver: DependencyResolver | None = None,
        rule_engine: StaticAnalysisRuleEngine | None = None,
        circular_engine: CircularDependencyEngine | None = None,
        dead_object_engine: DeadObjectEngine | None = None,
    ) -> None:
        self._parser = parser or SQLParser()
        self._resolver = resolver or DependencyResolver()
        self._rule_engine = rule_engine or StaticAnalysisRuleEngine()
        self._circular_engine = circular_engine or CircularDependencyEngine()
        self._dead_object_engine = dead_object_engine or DeadObjectEngine()

    @staticmethod
    def _normalize_entry_points(entry_points: Iterable[str]) -> tuple[str, ...]:
        canonical: dict[str, str] = {}
        for raw in entry_points:
            name = raw.strip()
            if not name:
                raise ValueError("Entry point name cannot be empty")
            canonical.setdefault(name.casefold(), name)
        return tuple(sorted(canonical.values(), key=str.casefold))

    @staticmethod
    def _canonical_sources(sources: Iterable[SqlSource]) -> tuple[SqlSource, ...]:
        by_id: dict[str, SqlSource] = {}
        for source in sources:
            key = source.source_id.casefold()
            if key in by_id:
                raise ValueError(f"Duplicate SQL source id: {source.source_id}")
            by_id[key] = source
        return tuple(sorted(by_id.values(), key=lambda item: item.source_id.casefold()))

    def analyze(
        self,
        sources: Iterable[SqlSource],
        *,
        entry_points: Iterable[str] = (),
        rule_ids: Iterable[str] = (),
    ) -> RepositoryAnalysisResult:
        canonical_sources = self._canonical_sources(sources)
        documents = tuple(
            self._parser.parse_source(source)
            for source in canonical_sources
        )
        graph = self._resolver.resolve(documents)
        canonical_entry_points = self._normalize_entry_points(entry_points)

        context = RuleContext(
            documents=documents,
            graph=graph,
            entry_points=canonical_entry_points,
        )
        static_analysis = self._rule_engine.run(context, rule_ids=rule_ids)
        cycles = self._circular_engine.detect(graph)
        dead_objects = self._dead_object_engine.detect(
            graph,
            entry_points=canonical_entry_points,
        )
        dead_objects = replace(
            dead_objects,
            dynamic_sql_object_count=context.dynamic_sql_object_count,
        )

        source_records: list[RepositorySourceRecord] = []
        object_records: list[RepositoryObjectRecord] = []
        for source, document in zip(canonical_sources, documents, strict=True):
            local_names = tuple(sql_object.qualified_name for sql_object in document.objects)
            source_records.append(
                RepositorySourceRecord(
                    source_id=source.source_id,
                    path=source.path,
                    objects=local_names,
                )
            )
            for sql_object in document.objects:
                name = sql_object.qualified_name
                object_records.append(
                    RepositoryObjectRecord(
                        name=name,
                        object_type=sql_object.object_type,
                        source_id=source.source_id,
                        dynamic_sql=sql_object.dynamic_sql,
                        dependencies=tuple(
                            node.name for node in graph.dependencies_of(name)
                        ),
                        dependents=tuple(
                            node.name for node in graph.dependents_of(name)
                        ),
                    )
                )

        return RepositoryAnalysisResult(
            sources=tuple(source_records),
            objects=tuple(
                sorted(
                    object_records,
                    key=lambda item: (item.name.casefold(), item.source_id.casefold()),
                )
            ),
            graph=graph,
            cycles=cycles,
            dead_objects=dead_objects,
            static_analysis=static_analysis,
            entry_points=canonical_entry_points,
        )
