from __future__ import annotations

from typing import Sequence

from ..ast import Token
from ..context import ParserContext


class StatementParser:
    def parse(self, statement_tokens: Sequence[Token], context: ParserContext) -> bool:
        raise NotImplementedError
