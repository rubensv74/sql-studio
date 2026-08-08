from __future__ import annotations

from typing import Sequence

from ..ast import Parameter, SqlObject, Token
from ..context import ParserContext
from ..names import split_qualified_name
from ..token_stream import TokenStream
from .base import StatementParser


class CreateStatementParser(StatementParser):
    _OBJECT_TYPES = {
        "PROCEDURE": "Stored Procedure",
        "VIEW": "View",
        "FUNCTION": "Function",
        "TRIGGER": "Trigger",
        "TABLE": "Table",
    }
    _MODULE_TYPES = {"Stored Procedure", "View", "Function", "Trigger"}

    def parse(self, statement_tokens: Sequence[Token], context: ParserContext) -> bool:
        if not statement_tokens:
            return False

        create_index = self._find_create_index(statement_tokens)
        if create_index is None:
            return False

        object_type, object_keyword_index = self._find_object_type(
            statement_tokens,
            create_index,
        )
        if object_type is None or object_keyword_index is None:
            return False

        name, schema, name_index = self._extract_name_and_schema(
            statement_tokens,
            object_keyword_index,
        )

        if object_type == "Table" and name is not None and name.startswith("#"):
            context.add_temporary_table(name)
            return True

        if (
            context.current_object is not None
            and context.current_object.object_type in self._MODULE_TYPES
            and object_type == "Table"
            and create_index == 0
        ):
            return False

        object_name = name or f"Unnamed{object_type}"
        context.add_object(
            SqlObject(name=object_name, schema=schema, object_type=object_type)
        )

        if object_type in {"Stored Procedure", "Function"} and name_index is not None:
            parameter_start = name_index + 1
            if (
                parameter_start < len(statement_tokens)
                and statement_tokens[parameter_start].value == "("
            ):
                parameter_start += 1

            self._parse_parameter_list(
                TokenStream(list(statement_tokens[parameter_start:])),
                context,
                stop_keywords={"AS", "RETURNS", "WITH", "BEGIN"},
            )

        return True

    @staticmethod
    def _find_create_index(tokens: Sequence[Token]) -> int | None:
        return next(
            (
                index
                for index, token in enumerate(tokens)
                if token.kind == "identifier" and token.value.upper() == "CREATE"
            ),
            None,
        )

    def _find_object_type(
        self,
        tokens: Sequence[Token],
        create_index: int,
    ) -> tuple[str | None, int | None]:
        for index in range(create_index + 1, len(tokens)):
            token = tokens[index]
            if token.kind != "identifier":
                continue
            value = token.value.upper()
            if value in {"OR", "ALTER"}:
                continue
            object_type = self._OBJECT_TYPES.get(value)
            if object_type is not None:
                return object_type, index

            if value in {
                "INDEX",
                "UNIQUE",
                "CLUSTERED",
                "NONCLUSTERED",
                "SCHEMA",
                "TYPE",
                "SYNONYM",
                "SEQUENCE",
                "DATABASE",
            }:
                if value not in {"UNIQUE", "CLUSTERED", "NONCLUSTERED"}:
                    return None, None
        return None, None

    @staticmethod
    def _extract_name_and_schema(
        tokens: Sequence[Token],
        object_keyword_index: int,
    ) -> tuple[str | None, str | None, int | None]:
        for index in range(object_keyword_index + 1, len(tokens)):
            token = tokens[index]
            if token.kind != "identifier" or token.value.startswith("@"):
                continue
            name, schema, _database = split_qualified_name(token.value)
            return name, schema, index
        return None, None, None

    def _parse_parameter_list(
        self,
        stream: TokenStream,
        context: ParserContext,
        *,
        stop_keywords: set[str],
    ) -> None:
        while not stream.is_at_end():
            token = stream.current()
            if token is None:
                break
            if token.value == ")":
                break
            if token.kind == "identifier" and token.value.upper() in stop_keywords:
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
                    if (
                        current.kind == "identifier"
                        and current.value.upper() in stop_keywords
                    ):
                        break
                    if (
                        current.kind == "identifier"
                        and current.value.upper() in {"OUTPUT", "OUT"}
                    ):
                        output = True
                        stream.advance()
                        continue
                    if current.value == "=":
                        stream.advance()
                        next_token = stream.advance()
                        if next_token is not None:
                            default_value = next_token.value
                        continue
                    if (
                        current.kind == "identifier"
                        and datatype is None
                    ):
                        datatype = current.value
                        stream.advance()
                        continue
                    stream.advance()
                context.add_parameter(
                    Parameter(
                        name=name,
                        datatype=datatype,
                        default_value=default_value,
                        output=output,
                    )
                )
                continue

            stream.advance()
