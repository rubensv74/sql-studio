from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .models import CrossReference


class CrossReferenceSerializer:
    """Serialize cross-references using a stable, versioned JSON schema."""

    SCHEMA_VERSION = "1.0"

    @classmethod
    def to_dict(
        cls,
        references: Iterable[CrossReference],
    ) -> dict[str, Any]:
        """Return a deterministic dictionary representation."""

        items = sorted(
            set(references),
            key=lambda reference: (
                reference.source.casefold(),
                reference.target.casefold(),
                reference.reference_type.value,
            ),
        )
        return {
            "schema_version": cls.SCHEMA_VERSION,
            "cross_references": [
                {
                    "source": reference.source,
                    "target": reference.target,
                    "type": reference.reference_type.value,
                }
                for reference in items
            ],
        }

    @classmethod
    def to_json(
        cls,
        references: Iterable[CrossReference],
        *,
        indent: int | None = 2,
    ) -> str:
        """Return UTF-8-safe JSON with deterministic key ordering."""

        return json.dumps(
            cls.to_dict(references),
            ensure_ascii=False,
            indent=indent,
            sort_keys=True,
        )

    @classmethod
    def write_json(
        cls,
        references: Iterable[CrossReference],
        path: str | Path,
        *,
        indent: int | None = 2,
    ) -> Path:
        """Write serialized cross-references and return the output path."""

        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            cls.to_json(references, indent=indent) + "\n",
            encoding="utf-8",
        )
        return output_path
