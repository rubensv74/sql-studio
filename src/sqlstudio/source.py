from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


def normalize_source_id(value: str) -> str:
    """Return a stable slash-normalized source identifier."""

    normalized = value.strip().replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    if not normalized:
        raise ValueError("SQL source id cannot be empty")
    return normalized


@dataclass(frozen=True)
class SqlSource:
    """Physical SQL input with caller-controlled stable identity.

    ``source_id`` identifies the physical repository source independently from
    SQL schema-object names. Durable definitions keep their normal SQL names;
    the source identity is used only when a file contains script-level evidence
    without a durable owner.
    """

    source_id: str
    sql_text: str
    path: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_id", normalize_source_id(self.source_id))

    @property
    def script_object_name(self) -> str:
        return f"script:{self.source_id}"

    @classmethod
    def from_path(cls, path: str | Path, *, source_id: str | None = None) -> "SqlSource":
        source_path = Path(path)
        identifier = source_id if source_id is not None else source_path.as_posix()
        return cls(
            source_id=identifier,
            sql_text=source_path.read_text(encoding="utf-8", errors="ignore"),
            path=str(source_path),
        )
