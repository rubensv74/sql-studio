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

        # Local/global temporary tables are execution-scoped implementation
        # details, not durable repository objects. Recording them only in the
        # active scope prevents a temp table from replacing its procedure or
        # from becoming the primary object of a utility script.
        if object_type == "Table" and name is not None and name.startswith("#"):
            context.add_temporary_table(name)
            return True

        # A permanent CREATE TABLE encountered while already inside a module is
        # runtime DDL owned by that module, not a second repository definition.
        # Top-level durable definitions are separated by GO or another top-level
        # CREATE scope. This guard prevents stored-procedure body DDL from
        # stealing ownership from the module being parsed.
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
            opening_index = next(
                (
                    index
                    for index in range(name_index + 1, len(statement_tokens))
                    if statement_tokens[index].value == "("
                ),
                None,
            )
            if opening_index is not None:
                self._parse_parameter_list(
                    TokenStream(list(statement_tokens[opening_index + 1 :])),
                    context,
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

            # Once an unsupported CREATE target is established (INDEX,
            # SCHEMA, TYPE, etc.), do not accidentally reinterpret a later
            # TABLE/VIEW token as the object kind for this statement.
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
    ) -> None:
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
                        break
                    if (
                        current.kind == "identifier"
                        and datatype is None
                        and current.value.upper()
                        not in {"AS", "RETURNS", "BEGIN", "END"}
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
