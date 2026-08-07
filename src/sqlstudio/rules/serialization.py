from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import StaticAnalysisResult


class StaticAnalysisSerializer:
    """Serialize consolidated static-analysis rule results deterministically."""

    SCHEMA_VERSION = "1.0"

    @staticmethod
    def _properties(items: tuple[tuple[str, str | int | bool], ...]) -> dict[str, str | int | bool]:
        return {key: value for key, value in items}

    @classmethod
    def to_dict(cls, result: StaticAnalysisResult) -> dict[str, Any]:
        findings = result.findings
        return {
            "schema_version": cls.SCHEMA_VERSION,
            "summary": {
                "rule_count": len(result.rule_results),
                "finding_count": len(findings),
                "error_count": result.count("error"),
                "warning_count": result.count("warning"),
                "info_count": result.count("info"),
                "parsed_object_count": result.parsed_object_count,
                "graph_node_count": result.graph_node_count,
                "dependency_edge_count": result.dependency_edge_count,
                "dynamic_sql_object_count": result.dynamic_sql_object_count,
            },
            "context": {
                "entry_points": list(result.entry_points),
                "static_analysis_only": True,
            },
            "rules": [
                {
                    "rule_id": rule_result.rule_id,
                    "title": rule_result.title,
                    "default_severity": rule_result.default_severity.value,
                    "finding_count": len(rule_result.findings),
                    "properties": cls._properties(rule_result.properties),
                }
                for rule_result in result.rule_results
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
        }

    @classmethod
    def to_json(cls, result: StaticAnalysisResult, *, indent: int | None = 2) -> str:
        return json.dumps(
            cls.to_dict(result),
            ensure_ascii=False,
            indent=indent,
            sort_keys=False,
        )

    @classmethod
    def write_json(
        cls,
        result: StaticAnalysisResult,
        destination: str | Path,
        *,
        indent: int | None = 2,
    ) -> Path:
        path = Path(destination)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(cls.to_json(result, indent=indent) + "\n", encoding="utf-8")
        return path
