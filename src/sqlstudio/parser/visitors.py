from __future__ import annotations

from .ast import SqlDocument, SqlObject


class SqlDocumentVisitor:
    def visit_document(self, document: SqlDocument) -> None:
        for obj in document.objects:
            self.visit_object(obj)

    def visit_object(self, obj: SqlObject) -> None:
        pass
