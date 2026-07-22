from __future__ import annotations

from typing import Sequence

from ..ast import Token
from ..context import ParserContext
from ..token_stream import TokenStream
from .base import StatementParser


class ExecutionStatementParser(StatementParser):
    def parse(self, statement_tokens: Sequence[Token], context: ParserContext) -> bool:
        if not statement_tokens:
            return False
        stream = TokenStream(list(statement_tokens))
        if stream.match_keyword("EXEC", "EXECUTE"):
            context.dynamic_sql = True
            context.add_reference("EXEC", kind="call")
            return True
        if stream.match_keyword("SP_EXECUTESQL"):
            context.dynamic_sql = True
            context.add_reference("sp_executesql", kind="call")
            return True
        return False
