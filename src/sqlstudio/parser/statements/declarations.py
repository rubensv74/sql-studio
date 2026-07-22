from __future__ import annotations

from typing import Sequence

from ..ast import Token
from ..context import ParserContext
from ..token_stream import TokenStream
from .base import StatementParser


class DeclarationStatementParser(StatementParser):
    def parse(self, statement_tokens: Sequence[Token], context: ParserContext) -> bool:
        if not statement_tokens:
            return False
        stream = TokenStream(list(statement_tokens))
        if not stream.match_keyword("DECLARE") and not stream.match_keyword("SET"):
            return False

        token = stream.current()
        if token is None or token.kind != "identifier":
            return True
        if token.value.startswith("@"):
            context.add_variable(token.value)
        return True
