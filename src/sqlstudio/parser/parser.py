from __future__ import annotations

from dataclasses import replace
from typing import List, Sequence

from sqlstudio.source import SqlSource

from .ast import SqlDocument, Token
from .context import ParserContext
from .statements import (
    CreateStatementParser,
    DeclarationStatementParser,
    ExecutionStatementParser,
    ReferenceStatementParser,
)
from .tokenizer import SQLTokenizer


class SQLParser:
    def __init__(self) -> None:
        self._tokens: List[Token] = []
        self._sql_text = ""

    def parse(self, sql_text: str) -> SqlDocument:
        """Parse raw SQL text using the historical text-only contract."""

        return self._parse(sql_text)

    def parse_source(self, source: SqlSource) -> SqlDocument:
        """Parse a physical source and give script-only scopes stable identity."""

        document = self._parse(source.sql_text)
        objects = [
            replace(sql_object, name=source.script_object_name)
            if sql_object.object_type == "Script" and sql_object.name == "UnnamedScript"
            else sql_object
            for sql_object in document.objects
        ]
        return SqlDocument(sql_text=document.sql_text, objects=objects, tokens=document.tokens)

    def _parse(self, sql_text: str) -> SqlDocument:
        if not sql_text or not sql_text.strip():
            return SqlDocument(sql_text=sql_text, objects=[])

        tokenizer = SQLTokenizer(sql_text)
        tokens = tokenizer.tokenize()
        self._tokens = tokens
        self._sql_text = sql_text

        context = ParserContext(tokens=tokens)
        self._parse_statements(context)
        context.finalize_current_object()

        return SqlDocument(sql_text=sql_text, objects=context.objects, tokens=tokens)

    def _parse_statements(self, context: ParserContext) -> None:
        statement_tokens: List[Token] = []
        for token in context.tokens:
            if self._is_batch_separator(token):
                self._parse_statement(statement_tokens, context)
                statement_tokens = []
                context.end_batch()
                continue

            if token.value == ";":
                self._parse_statement(statement_tokens, context)
                statement_tokens = []
                continue

            statement_tokens.append(token)

        if statement_tokens:
            self._parse_statement(statement_tokens, context)

    def _parse_statement(
        self,
        statement_tokens: Sequence[Token],
        context: ParserContext,
    ) -> None:
        if not statement_tokens:
            return
        filtered = [token for token in statement_tokens if token.value != ";"]
        if not filtered:
            return

        parsers = [
            CreateStatementParser(),
            DeclarationStatementParser(),
            ExecutionStatementParser(),
            ReferenceStatementParser(),
        ]
        for parser in parsers:
            parser.parse(filtered, context)

        for token in filtered:
            if token.kind == "identifier" and token.value.startswith("#"):
                context.add_temporary_table(token.value)

    def _is_batch_separator(self, token: Token) -> bool:
        """Return True only for ``GO`` written as a standalone source line."""

        if token.kind != "identifier" or token.value.upper() != "GO":
            return False

        line_start = self._sql_text.rfind("\n", 0, token.position) + 1
        line_end = self._sql_text.find("\n", token.position)
        if line_end == -1:
            line_end = len(self._sql_text)

        return self._sql_text[line_start:line_end].strip().upper() == "GO"
