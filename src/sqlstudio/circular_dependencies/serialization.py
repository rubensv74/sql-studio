from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from .models import CircularDependency


class CircularDependencySerializer:
    """Serialize circular dependency findings deterministically."""

    SCHEMA_VERSION = "1.0"

    @classmethod
    def to_dict(
        cls,
        cycles: Iterable[CircularDependency],
    ) -> dict[str, Any]:
        ordered = tuple(cycles)
        return {
            "schema_version": cls.SCHEMA_VERSION,
            "summary": {
                "cycle_count": len(ordered),
                "object_count": sum(len(cycle.members) for cycle in ordered),
            },
            "circular_dependencies": [
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
                for cycle in ordered
            ],
        }

    @classmethod
    def to_json(
        cls,
        cycles: Iterable[CircularDependency],
        *,
        indent: int | None = 2,
    ) -> str:
        return json.dumps(
            cls.to_dict(cycles),
            ensure_ascii=False,
            indent=indent,
            sort_keys=False,
        )

    @classmethod
    def write_json(
        cls,
        cycles: Iterable[CircularDependency],
        destination: str | Path,
        *,
        indent: int | None = 2,
    ) -> Path:
        path = Path(destination)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(cls.to_json(cycles, indent=indent) + "\n", encoding="utf-8")
        return path
