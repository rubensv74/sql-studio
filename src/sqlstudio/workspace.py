from pathlib import Path

from .scanner import RepositoryScanner


class Workspace:
    def __init__(self, root: str | Path):
        self.root = Path(root)

    def scan(self) -> dict:
        return RepositoryScanner(self.root).scan().to_dict()
