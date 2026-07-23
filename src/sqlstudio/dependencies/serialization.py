from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .graph import DependencyGraph


class DependencyGraphSerializer:
    """Serialize dependency graphs using a deterministic JSON representation."""

    SCHEMA_VERSION = 1

    @classmethod
    def to_dict(cls, graph: DependencyGraph) -> dict[str, Any]:
        """Return a stable, JSON-compatible representation of ``graph``."""

        return {
            "schema_version": cls.SCHEMA_VERSION,
            "nodes": [
                {
                    "name": node.name,
                    "object_type": node.object_type,
                }
                for node in graph.nodes
            ],
            "edges": [
                {
                    "source": edge.source.name,
                    "target": edge.target.name,
                    "kind": edge.kind.value,
                }
                for edge in graph.edges
            ],
        }

    @classmethod
    def to_json(
        cls,
        graph: DependencyGraph,
        *,
        indent: int | None = 2,
    ) -> str:
        """Serialize ``graph`` to deterministic UTF-8 JSON text."""

        return json.dumps(
            cls.to_dict(graph),
            ensure_ascii=False,
            indent=indent,
            sort_keys=False,
        )

    @classmethod
    def write_json(
        cls,
        graph: DependencyGraph,
        destination: str | Path,
        *,
        indent: int | None = 2,
    ) -> Path:
        """Write a serialized graph to ``destination`` and return its path."""

        path = Path(destination)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(cls.to_json(graph, indent=indent) + "\n", encoding="utf-8")
        return path
