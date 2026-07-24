import json
from typing import Any, Dict

from .models import ImpactResult


class ImpactResultSerializer:
    SCHEMA_VERSION = "1.0"

    @classmethod
    def to_dict(cls, result: ImpactResult) -> Dict[str, Any]:
        return {
            "schema_version": cls.SCHEMA_VERSION,
            "root_object": result.root_object,
            "impacted_objects": sorted(result.impacted_objects),
        }

    @classmethod
    def to_json(cls, result: ImpactResult, *, indent: int | None = 2) -> str:
        return json.dumps(
            cls.to_dict(result),
            ensure_ascii=False,
            indent=indent,
            sort_keys=True,
        )

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> ImpactResult:
        if payload.get("schema_version") != cls.SCHEMA_VERSION:
            raise ValueError(
                f"Unsupported impact result schema: {payload.get('schema_version')!r}"
            )

        root_object = payload.get("root_object")
        impacted_objects = payload.get("impacted_objects")

        if not isinstance(root_object, str) or not root_object.strip():
            raise ValueError("root_object must be a non-empty string")

        if not isinstance(impacted_objects, list) or not all(
            isinstance(item, str) for item in impacted_objects
        ):
            raise ValueError("impacted_objects must be a list of strings")

        return ImpactResult(
            root_object=root_object,
            impacted_objects=list(impacted_objects),
        )

    @classmethod
    def from_json(cls, payload: str) -> ImpactResult:
        data = json.loads(payload)
        if not isinstance(data, dict):
            raise ValueError("Impact result JSON must contain an object")
        return cls.from_dict(data)
