import re
from pathlib import Path
from typing import List, Sequence

from .models import ProjectIndex, SqlFileEntry


class ClassificationRule:
    def __init__(self, kind: str, pattern: str):
        self.kind = kind
        self.pattern = re.compile(pattern, re.IGNORECASE)

    def matches(self, content: str) -> bool:
        return bool(self.pattern.search(content))


class SqlClassifier:
    def __init__(self, rules: Sequence[ClassificationRule] | None = None):
        self.rules = list(rules or self._default_rules())

    def classify(self, content: str) -> str:
        normalized = content.upper()
        for rule in self.rules:
            if rule.matches(normalized):
                return rule.kind
        return "Script"

    @staticmethod
    def _default_rules() -> List[ClassificationRule]:
        return [
            ClassificationRule("Stored Procedure", r"\bCREATE\s+(OR\s+ALTER\s+)?PROCEDURE\b"),
            ClassificationRule("View", r"\bCREATE\s+VIEW\b"),
            ClassificationRule("Function", r"\bCREATE\s+FUNCTION\b"),
        ]


class RepositoryScanner:
    def __init__(self, root: str | Path, classifier: SqlClassifier | None = None):
        self.root = Path(root)
        self.classifier = classifier or SqlClassifier()

    def scan(self) -> ProjectIndex:
        files: List[SqlFileEntry] = []
        for path in sorted(self.root.rglob("*.sql")):
            if not path.is_file():
                continue
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
            except PermissionError as exc:
                raise PermissionError(f"Unable to read SQL file: {path}") from exc
            except OSError as exc:
                raise OSError(f"Unable to read SQL file: {path}") from exc

            files.append(
                SqlFileEntry(
                    path=str(path),
                    name=path.name,
                    kind=self.classifier.classify(content),
                    content=content,
                )
            )
        return ProjectIndex(root=str(self.root), files=files)
