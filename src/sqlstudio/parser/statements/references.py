from __future__ import annotations

from typing import Sequence

from ..ast import Token
from ..context import ParserContext
from ..token_stream import TokenStream
from .base import StatementParser


class ReferenceStatementParser(StatementParser):
    def parse(self, statement_tokens: Sequence[Token], context: ParserContext) -> bool:
        if not statement_tokens:
            return False
        stream = TokenStream(list(statement_tokens))
        keywords = {"FROM", "JOIN", "UPDATE", "INTO", "DELETE", "MERGE", "OPENQUERY", "OPENROWSET"}
        while not stream.is_at_end():
            token = stream.current()
            if token is None:
                break
            if token.kind == "identifier" and token.value.upper() in keywords:
                stream.advance()
                next_token = stream.current()
                if next_token is not None and next_token.kind == "identifier":
                    parts = next_token.value.split(".")
                    if len(parts) == 1:
                        context.add_reference(parts[0])
                    else:
                        context.add_reference(parts[-1], schema=parts[-2] if len(parts) > 1 else None, database=parts[0] if len(parts) > 2 else None)
                break
            stream.advance()
        return True
