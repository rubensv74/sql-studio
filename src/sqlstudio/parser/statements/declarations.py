from __future__ import annotations

from typing import Sequence

from ..ast import Token
from ..context import ParserContext
from .base import StatementParser


class DeclarationStatementParser(StatementParser):
    def parse(self, statement_tokens: Sequence[Token], context: ParserContext) -> bool:
        """Collect DECLARE/SET variables wherever they occur in a statement.

        The first statement of a stored module commonly contains the CREATE
        header, AS/BEGIN and the first DECLARE before the first semicolon. A
        start-token-only parser therefore misses that declaration. Scanning for
        the declaration keyword also ensures the variable is attributed to the
        object scope established by creation parsing earlier in the pipeline.
        """

        found = False
        for index, token in enumerate(statement_tokens[:-1]):
            if token.kind != "identifier":
                continue
            if token.value.upper() not in {"DECLARE", "SET"}:
                continue

            candidate = statement_tokens[index + 1]
            if candidate.kind == "identifier" and candidate.value.startswith("@"):
                context.add_variable(candidate.value)
                found = True

        return found
