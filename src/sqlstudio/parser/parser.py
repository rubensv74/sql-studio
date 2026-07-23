from __future__ import annotations

from typing import List, Sequence

from .ast import Parameter, Reference, SqlDocument, SqlObject, Token, Variable
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

    def parse(self, sql_text: str) -> SqlDocument:
        if not sql_text or not sql_text.strip():
            return SqlDocument(sql_text=sql_text, objects=[])

        tokenizer = SQLTokenizer(sql_text)
        tokens = tokenizer.tokenize()
        self._tokens = tokens

        context = ParserContext(tokens=tokens)
        self._parse_statements(context)

        if context.objects:
            first_object = context.objects[0]
            object_with_details = SqlObject(
                name=first_object.name,
                schema=first_object.schema,
                object_type=first_object.object_type,
                parameters=context.parameters,
                variables=context.variables,
                references=context.references,
                temporary_tables=context.temporary_tables,
                dynamic_sql=context.dynamic_sql,
            )
            context.objects = [object_with_details]

        return SqlDocument(sql_text=sql_text, objects=context.objects, tokens=tokens)

    def _parse_statements(self, context: ParserContext) -> None:
        statement_tokens: List[Token] = []
        for token in context.tokens:
            if token.value == ";":
                self._parse_statement(statement_tokens, context)
                statement_tokens = []
                continue
            if token.kind == "identifier" and token.value.startswith("#"):
                context.add_temporary_table(token.value)
            statement_tokens.append(token)
        if statement_tokens:
            self._parse_statement(statement_tokens, context)

    def _parse_statement(self, statement_tokens: Sequence[Token], context: ParserContext) -> None:
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
            if parser.parse(filtered, context):
                break

    def _find_object_type(self, tokens: List[Token], start: int) -> str | None:
        return None

    def _extract_name(self, tokens: List[Token], start: int) -> str | None:
        return None
