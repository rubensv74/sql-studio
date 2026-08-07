from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import DeadObjectResult


class DeadObjectSerializer:
    """Serialize dead-object candidate analysis deterministically."""

    SCHEMA_VERSION = "1.0"

    @classmethod
    def to_dict(cls, result: DeadObjectResult) -> dict[str, Any]:
        candidate_object_count = sum(
            len(finding.members) for finding in result.findings
        )
        return {
            "schema_version": cls.SCHEMA_VERSION,
            "classification": "candidate_only",
            "summary": {
                "defined_object_count": result.defined_object_count,
                "candidate_finding_count": len(result.findings),
                "candidate_object_count": candidate_object_count,
                "excluded_object_count": len(result.excluded_objects),
                "declared_entry_point_count": len(result.entry_points),
                "dynamic_sql_object_count": result.dynamic_sql_object_count,
            },
            "limitations": {
                "external_usage_may_exist": True,
                "dynamic_sql_may_hide_dependencies": result.dynamic_sql_object_count > 0,
                "safe_to_delete": False,
            },
            "entry_points": list(result.entry_points),
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
                }
                for finding in result.findings
            ],
            "excluded_objects": [
                {
                    "name": exclusion.name,
                    "object_type": exclusion.object_type,
                    "reason": exclusion.reason,
                }
                for exclusion in result.excluded_objects
            ],
        }

    @classmethod
    def to_json(
        cls,
        result: DeadObjectResult,
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
        result: DeadObjectResult,
        destination: str | Path,
        *,
        indent: int | None = 2,
    ) -> Path:
        path = Path(destination)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(cls.to_json(result, indent=indent) + "\n", encoding="utf-8")
        return path
