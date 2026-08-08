from __future__ import annotations

from typing import Sequence

from ..ast import Parameter, SqlObject, Token
from ..context import ParserContext
from ..names import split_qualified_name
from ..token_stream import TokenStream
from .base import StatementParser


class CreateStatementParser(StatementParser):
    def parse(self, statement_tokens: Sequence[Token], context: ParserContext) -> bool:
        if not statement_tokens:
            return False
        stream = TokenStream(list(statement_tokens))
        if not stream.match_keyword("CREATE"):
            return False
        stream.match_keyword("OR")
        stream.match_keyword("ALTER")

        object_type = self._find_object_type(statement_tokens)
        if object_type is None:
            return False

        name, schema = self._extract_name_and_schema(statement_tokens, 0)

        # Local/global temporary tables are execution-scoped implementation
        # details, not durable repository objects. Recording them only in the
        # temporary-table collection also prevents a utility script whose first
        # CREATE is temporary from being misclassified as a durable Table.
        if object_type == "Table" and name is not None and name.startswith("#"):
            context.add_temporary_table(name)
            return True

        object_name = name or f"Unnamed{object_type}"
        context.add_object(SqlObject(name=object_name, schema=schema, object_type=object_type))

        opening_index = next((index for index, token in enumerate(statement_tokens) if token.value == "("), None)
        if opening_index is not None:
            self._parse_parameter_list(TokenStream(list(statement_tokens[opening_index + 1:])), context)

        return True

    def _find_object_type(self, tokens: Sequence[Token]) -> str | None:
        for token in tokens:
            if token.kind != "identifier":
                continue
            value = token.value.upper()
            if value in {"OR", "ALTER", "CREATE"}:
                continue
            if value == "PROCEDURE":
                return "Stored Procedure"
            if value == "VIEW":
                return "View"
            if value == "FUNCTION":
                return "Function"
            if value == "TRIGGER":
                return "Trigger"
            if value == "TABLE":
                return "Table"
        return None

    def _extract_name_and_schema(self, tokens: Sequence[Token], start: int) -> tuple[str | None, str | None]:
        object_keywords = {"PROCEDURE", "VIEW", "FUNCTION", "TRIGGER", "TABLE"}
        object_keyword_index = next(
            (
                index
                for index, token in enumerate(tokens[start:], start=start)
                if token.kind == "identifier" and token.value.upper() in object_keywords
            ),
            None,
        )
        if object_keyword_index is None:
            return None, None

        for token in tokens[object_keyword_index + 1 :]:
            if token.kind != "identifier" or token.value.startswith("@"):
                continue
            name, schema, _database = split_qualified_name(token.value)
            return name, schema

        return None, None

    def _parse_parameter_list(self, stream: TokenStream, context: ParserContext) -> None:
        while not stream.is_at_end():
            token = stream.current()
            if token is None:
                break
            if token.value == ")":
                break
            if token.value == ",":
                stream.advance()
                continue

            if token.kind == "identifier" and token.value.startswith("@"):
                name = token.value
                stream.advance()
                datatype: str | None = None
                default_value: str | None = None
                output = False
                while not stream.is_at_end():
                    current = stream.current()
                    if current is None:
                        break
                    if current.value in {",", ")"}:
                        break
                    if current.kind == "identifier" and current.value.upper() in {"OUTPUT", "OUT"}:
                        output = True
                        stream.advance()
                        continue
                    if current.value == "=":
                        stream.advance()
                        next_token = stream.advance()
                        if next_token is not None:
                            default_value = next_token.value
                        break
                    if current.kind == "identifier" and datatype is None and current.value.upper() not in {"AS", "RETURNS", "BEGIN", "END"}:
                        datatype = current.value
                        stream.advance()
                        continue
                    stream.advance()
                context.add_parameter(Parameter(name=name, datatype=datatype, default_value=default_value, output=output))
                continue

            stream.advance()
