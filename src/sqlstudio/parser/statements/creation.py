from __future__ import annotations

from typing import Sequence

from ..ast import Parameter, SqlObject, Token
from ..context import ParserContext
from ..names import split_qualified_name
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
            parameter_tokens = list(statement_tokens[name_index + 1 :])
            wrapped = bool(parameter_tokens and parameter_tokens[0].value == "(")
            if wrapped:
                parameter_tokens = parameter_tokens[1:]

            self._parse_parameter_list(
                parameter_tokens,
                context,
                stop_keywords={"AS", "RETURNS", "WITH", "BEGIN"},
                wrapped=wrapped,
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
        tokens: Sequence[Token],
        context: ParserContext,
        *,
        stop_keywords: set[str],
        wrapped: bool,
    ) -> None:
        """Parse module parameters while respecting datatype parentheses.

        Procedure parameters do not require an outer parenthesized list, while
        functions commonly use one. Datatypes such as ``nvarchar(30)``,
        ``decimal(18,4)`` and ``datetime2(3)`` also contain parentheses. Their
        closing token must not be confused with the end of the parameter list.
        """

        index = 0
        while index < len(tokens):
            token = tokens[index]
            if self._is_parameter_list_end(token, depth=0, wrapped=wrapped, stop_keywords=stop_keywords):
                break
            if token.value == ",":
                index += 1
                continue
            if token.kind != "identifier" or not token.value.startswith("@"):
                index += 1
                continue

            name = token.value
            index += 1
            datatype: str | None = None
            default_value: str | None = None
            output = False
            depth = 0

            while index < len(tokens):
                current = tokens[index]

                if current.value == "(":
                    depth += 1
                    index += 1
                    continue

                if current.value == ")":
                    if depth > 0:
                        depth -= 1
                        index += 1
                        continue
                    if wrapped:
                        break
                    index += 1
                    continue

                if depth == 0 and current.value == ",":
                    index += 1
                    break

                if (
                    depth == 0
                    and current.kind == "identifier"
                    and current.value.upper() in stop_keywords
                ):
                    break

                if (
                    depth == 0
                    and current.kind == "identifier"
                    and current.value.upper() in {"OUTPUT", "OUT"}
                ):
                    output = True
                    index += 1
                    continue

                if depth == 0 and current.value == "=":
                    index += 1
                    if index < len(tokens):
                        default_value = tokens[index].value
                        index += 1
                    continue

                if current.kind == "identifier" and datatype is None:
                    datatype = current.value

                index += 1

            context.add_parameter(
                Parameter(
                    name=name,
                    datatype=datatype,
                    default_value=default_value,
                    output=output,
                )
            )

            if index < len(tokens) and self._is_parameter_list_end(
                tokens[index],
                depth=0,
                wrapped=wrapped,
                stop_keywords=stop_keywords,
            ):
                break

    @staticmethod
    def _is_parameter_list_end(
        token: Token,
        *,
        depth: int,
        wrapped: bool,
        stop_keywords: set[str],
    ) -> bool:
        if depth != 0:
            return False
        if wrapped and token.value == ")":
            return True
        return token.kind == "identifier" and token.value.upper() in stop_keywords
