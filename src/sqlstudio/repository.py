import json
from pathlib import Path
from typing import Optional

from .scanner import RepositoryScanner


class RepositoryEngine:
    def __init__(self, root: Optional[str | Path] = None):
        self.root = Path(root) if root is not None else Path.cwd()
        self.index = None

    def scan(self, root: Optional[str | Path] = None) -> dict:
        target = Path(root) if root is not None else self.root
        self._validate_root(target)
        self.index = RepositoryScanner(target).scan()
        return self.index.to_dict()

    def to_json(self, root: Optional[str | Path] = None) -> str:
        return json.dumps(self.scan(root), indent=2)

    def _validate_root(self, path: Path) -> None:
        if not path.exists():
            raise FileNotFoundError(f"Repository path does not exist: {path}")
        if not path.is_dir():
            raise NotADirectoryError(f"Repository path is not a directory: {path}")
