#!/usr/bin/env python3
"""Compatibility wrapper for running SQL Studio directly from a repository checkout."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
src_root_text = str(SRC_ROOT)
while src_root_text in sys.path:
    sys.path.remove(src_root_text)
sys.path.insert(0, src_root_text)

from sqlstudio.cli import (
    _collect_sql_files,
    _read_sql_sources,
    analyze_circular_dependencies,
    analyze_cross_references,
    analyze_dead_objects,
    analyze_dependencies,
    analyze_impact,
    analyze_repository,
    analyze_static_rules,
    build_parser,
    create_handoff,
    create_sprint,
    main,
    parse_sql_file,
    scan_repository,
)


def _read_sql_texts(paths, *, recursive=False):
    """Legacy wrapper helper retained for repository-checkout compatibility."""

    return [source.sql_text for source in _read_sql_sources(paths, recursive=recursive)]


__all__ = [
    "_collect_sql_files",
    "_read_sql_texts",
    "_read_sql_sources",
    "analyze_circular_dependencies",
    "analyze_cross_references",
    "analyze_dead_objects",
    "analyze_dependencies",
    "analyze_impact",
    "analyze_repository",
    "analyze_static_rules",
    "build_parser",
    "create_handoff",
    "create_sprint",
    "main",
    "parse_sql_file",
    "scan_repository",
]


if __name__ == "__main__":
    raise SystemExit(main())
