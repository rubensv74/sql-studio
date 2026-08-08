from __future__ import annotations

from typing import List, Sequence

from sqlstudio.source import SqlSource

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
        self._sql_text = ""

    def parse(self, sql_text: str) -> SqlDocument:
        """Parse raw SQL text using the historical text-only contract."""

        return self._parse(sql_text)

    def parse_source(self, source: SqlSource) -> SqlDocument:
        """Parse one physical source with one stable fallback Script identity.

        Object-scoped parsing may materialize several internal Script scopes when
        durable definitions or ``GO`` batches split a physical file. The
        source-aware contract aggregates all fallback script evidence from that
        file into one ``script:<source_id>`` object while leaving durable objects
        untouched.
        """

        document = self._parse(source.sql_text)
        script_scopes = [
            sql_object
            for sql_object in document.objects
            if self._is_fallback_script(sql_object)
        ]
        if not script_scopes:
            return document

        merged_script = self._merge_script_scopes(source, script_scopes)
        objects: list[SqlObject] = []
        script_inserted = False
        for sql_object in document.objects:
            if self._is_fallback_script(sql_object):
                if not script_inserted:
                    objects.append(merged_script)
                    script_inserted = True
                continue
            objects.append(sql_object)

        return SqlDocument(sql_text=document.sql_text, objects=objects, tokens=document.tokens)

    @staticmethod
    def _is_fallback_script(sql_object: SqlObject) -> bool:
        return sql_object.object_type == "Script" and sql_object.name == "UnnamedScript"

    @classmethod
    def _merge_script_scopes(
        cls,
        source: SqlSource,
        scopes: Sequence[SqlObject],
    ) -> SqlObject:
        return SqlObject(
            name=source.script_object_name,
            object_type="Script",
            parameters=cls._unique_parameters(scopes),
            variables=cls._unique_variables(scopes),
            references=cls._unique_references(scopes),
            temporary_tables=cls._unique_temporary_tables(scopes),
            dynamic_sql=any(scope.dynamic_sql for scope in scopes),
        )

    @staticmethod
    def _unique_parameters(scopes: Sequence[SqlObject]) -> list[Parameter]:
        seen: set[str] = set()
        result: list[Parameter] = []
        for scope in scopes:
            for parameter in scope.parameters:
                key = parameter.name.casefold()
                if key not in seen:
                    seen.add(key)
                    result.append(parameter)
        return result

    @staticmethod
    def _unique_variables(scopes: Sequence[SqlObject]) -> list[Variable]:
        seen: set[str] = set()
        result: list[Variable] = []
        for scope in scopes:
            for variable in scope.variables:
                key = variable.name.casefold()
                if key not in seen:
                    seen.add(key)
                    result.append(variable)
        return result

    @staticmethod
    def _unique_references(scopes: Sequence[SqlObject]) -> list[Reference]:
        seen: set[tuple[str | None, str | None, str, str]] = set()
        result: list[Reference] = []
        for scope in scopes:
            for reference in scope.references:
                key = (
                    reference.database.casefold() if reference.database else None,
                    reference.schema.casefold() if reference.schema else None,
                    reference.name.casefold(),
                    reference.kind.casefold(),
                )
                if key not in seen:
                    seen.add(key)
                    result.append(reference)
        return result

    @staticmethod
    def _unique_temporary_tables(scopes: Sequence[SqlObject]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for scope in scopes:
            for name in scope.temporary_tables:
                key = name.casefold()
                if key not in seen:
                    seen.add(key)
                    result.append(name)
        return result

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
