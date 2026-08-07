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

from sqlstudio.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
