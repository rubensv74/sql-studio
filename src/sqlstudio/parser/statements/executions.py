from __future__ import annotations

from typing import Sequence

from ..ast import Token
from ..context import ParserContext
from .base import StatementParser


class ExecutionStatementParser(StatementParser):
    def parse(self, statement_tokens: Sequence[Token], context: ParserContext) -> bool:
        if not statement_tokens:
            return False

        for index, token in enumerate(statement_tokens):
            if token.kind != "identifier":
                continue

            keyword = token.value.upper()
            if keyword not in {"EXEC", "EXECUTE", "SP_EXECUTESQL"}:
                continue

            reference_name = "sp_executesql" if keyword == "SP_EXECUTESQL" else self._target_name(
                statement_tokens,
                index + 1,
            )
            is_sp_executesql_target = (
                reference_name is not None
                and reference_name.split(".")[-1].casefold() == "sp_executesql"
            )
            context.dynamic_sql = (
                context.dynamic_sql
                or keyword == "SP_EXECUTESQL"
                or is_sp_executesql_target
                or reference_name is None
            )
            if reference_name is not None:
                parts = [part for part in reference_name.split(".") if part]
                context.add_reference(
                    parts[-1],
                    schema=parts[-2] if len(parts) > 1 else None,
                    database=parts[-3] if len(parts) > 2 else None,
                    kind="call",
                )
            return True

        return False

    @staticmethod
    def _target_name(statement_tokens: Sequence[Token], start: int) -> str | None:
        for token in statement_tokens[start:]:
            if token.kind == "identifier" and not token.value.startswith("@"):
                return token.value
            if token.value == "(":
                return None
        return None
