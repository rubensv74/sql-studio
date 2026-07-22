from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class SqlFileEntry:
    path: str
    name: str
    kind: str
    content: str | None = None


@dataclass(frozen=True)
class ProjectIndex:
    root: str
    files: List[SqlFileEntry]

    def to_dict(self) -> dict:
        return {
            "root": self.root,
            "files": [
                {
                    "path": item.path,
                    "name": item.name,
                    "kind": item.kind,
                }
                for item in self.files
            ],
            "summary": {
                "total_sql_files": len(self.files),
                "stored_procedures": sum(1 for item in self.files if item.kind == "Stored Procedure"),
                "views": sum(1 for item in self.files if item.kind == "View"),
                "functions": sum(1 for item in self.files if item.kind == "Function"),
                "scripts": sum(1 for item in self.files if item.kind == "Script"),
            },
        }
