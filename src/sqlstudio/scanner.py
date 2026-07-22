import re
from pathlib import Path
from typing import List

from .models import ProjectIndex, SqlFileEntry


class RepositoryScanner:
    def __init__(self, root: str | Path):
        self.root = Path(root)

    def scan(self) -> ProjectIndex:
        files: List[SqlFileEntry] = []
        for path in sorted(self.root.rglob("*.sql")):
            if not path.is_file():
                continue
            entry = SqlFileEntry(
                path=str(path),
                name=path.name,
                kind=self._classify(path.read_text(encoding="utf-8", errors="ignore")),
                content=path.read_text(encoding="utf-8", errors="ignore"),
            )
            files.append(entry)
        return ProjectIndex(root=str(self.root), files=files)

    def _classify(self, content: str) -> str:
        text = content.upper()
        if re.search(r"\bCREATE\s+OR\s+ALTER\s+PROCEDURE\b|\bCREATE\s+PROCEDURE\b", text):
            return "Stored Procedure"
        if re.search(r"\bCREATE\s+VIEW\b", text):
            return "View"
        if re.search(r"\bCREATE\s+FUNCTION\b", text):
            return "Function"
        return "Script"
