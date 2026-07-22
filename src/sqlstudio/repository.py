import json
from pathlib import Path
from typing import Optional

from .scanner import RepositoryScanner
from .workspace import Workspace


class RepositoryEngine:
    def __init__(self, root: Optional[str | Path] = None):
        self.root = Path(root) if root is not None else Path.cwd()
        self.index = None

    def scan(self, root: Optional[str | Path] = None) -> dict:
        target = Path(root) if root is not None else self.root
        self.index = RepositoryScanner(target).scan()
        return self.index.to_dict()

    def scan_workspace(self, root: Optional[str | Path] = None) -> dict:
        return Workspace(root or self.root).scan()

    def to_json(self, root: Optional[str | Path] = None) -> str:
        return json.dumps(self.scan(root), indent=2)
