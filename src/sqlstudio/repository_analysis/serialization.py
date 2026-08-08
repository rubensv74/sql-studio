from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlstudio.dependencies import DependencyGraphSerializer

from .models import RepositoryAnalysisResult


class RepositoryAnalysisSerializer:
    """Serialize the canonical repository-analysis result deterministically."""

    SCHEMA_VERSION = "1.0"

    @staticmethod
    def _properties(items: tuple[tuple[str, str | int | bool], ...]) -> dict[str, str | int | bool]:
        return {key: value for key, value in items}

    @classmethod
    def to_dict(cls, result: RepositoryAnalysisResult) -> dict[str, Any]:
        findings = result.static_analysis.findings
        dead_findings = result.dead_objects.findings
        dependency_payload = DependencyGraphSerializer.to_dict(result.graph)
        return {
            "schema_version": cls.SCHEMA_VERSION,
            "summary": {
                "source_count": result.source_count,
                "parsed_object_count": result.parsed_object_count,
                "durable_object_count": result.durable_object_count,
                "script_object_count": result.script_object_count,
                "graph_node_count": len(result.graph.nodes),
                "dependency_edge_count": len(result.graph.edges),
                "circular_component_count": len(result.cycles),
                "dead_object_candidate_count": len(dead_findings),
                "dead_object_candidate_object_count": sum(
                    len(finding.members) for finding in dead_findings
                ),
                "finding_count": len(findings),
                "error_count": result.static_analysis.count("error"),
                "warning_count": result.static_analysis.count("warning"),
                "info_count": result.static_analysis.count("info"),
                "dynamic_sql_object_count": len(result.dynamic_sql_objects),
            },
            "sources": [
                {
                    "source_id": source.source_id,
                    "path": source.path,
                    "objects": list(source.objects),
                }
                for source in result.sources
            ],
            "objects": [
                {
                    "name": item.name,
                    "object_type": item.object_type,
                    "source_id": item.source_id,
                    "dynamic_sql": item.dynamic_sql,
                    "dependencies": list(item.dependencies),
                    "dependents": list(item.dependents),
                    "dependency_count": item.dependency_count,
                    "dependent_count": item.dependent_count,
                }
                for item in result.objects
            ],
            "dependencies": {
                "nodes": dependency_payload["nodes"],
                "edges": dependency_payload["edges"],
            },
            "cycles": [
                {
                    "members": list(cycle.members),
                    "is_self_reference": cycle.is_self_reference,
                    "edges": [
                        {
                            "source": edge.source.name,
                            "target": edge.target.name,
                            "kind": edge.kind.value,
                        }
                        for edge in cycle.edges
                    ],
                }
                for cycle in result.cycles
            ],
            "dead_object_candidates": [
                {
                    "members": [
                        {
                            "name": member.name,
                            "object_type": member.object_type,
                        }
                        for member in finding.members
                    ],
                    "is_circular_component": finding.is_circular_component,
                    "reason": finding.reason,
                    "external_usage_possible": finding.external_usage_possible,
                    "safe_to_delete": False,
                }
                for finding in dead_findings
            ],
            "dead_object_exclusions": [
                {
                    "name": exclusion.name,
                    "object_type": exclusion.object_type,
                    "reason": exclusion.reason,
                }
                for exclusion in result.dead_objects.excluded_objects
            ],
            "rules": [
                {
                    "rule_id": rule_result.rule_id,
                    "title": rule_result.title,
                    "default_severity": rule_result.default_severity.value,
                    "finding_count": len(rule_result.findings),
                    "properties": cls._properties(rule_result.properties),
                }
                for rule_result in result.static_analysis.rule_results
            ],
            "findings": [
                {
                    "rule_id": finding.rule_id,
                    "severity": finding.severity.value,
                    "title": finding.title,
                    "message": finding.message,
                    "objects": list(finding.objects),
                    "properties": cls._properties(finding.properties),
                }
                for finding in findings
            ],
            "uncertainty": {
                "static_analysis_only": True,
                "dynamic_sql_object_count": len(result.dynamic_sql_objects),
                "dynamic_sql_objects": [
                    item.name for item in result.dynamic_sql_objects
                ],
            },
            "context": {
                "entry_points": list(result.entry_points),
                "dependency_direction": "source -> target",
                "dead_objects_are_candidates_only": True,
            },
        }

    @classmethod
    def to_json(
        cls,
        result: RepositoryAnalysisResult,
        *,
        indent: int | None = 2,
    ) -> str:
        return json.dumps(
            cls.to_dict(result),
            ensure_ascii=False,
            indent=indent,
            sort_keys=False,
        )

    @classmethod
    def write_json(
        cls,
        result: RepositoryAnalysisResult,
        destination: str | Path,
        *,
        indent: int | None = 2,
    ) -> Path:
        path = Path(destination)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(cls.to_json(result, indent=indent) + "\n", encoding="utf-8")
        return path
