from __future__ import annotations

from typing import List, Optional

from .ast import Token


class TokenStream:
    def __init__(self, tokens: List[Token]) -> None:
        self._tokens = tokens
        self._index = 0

    def current(self) -> Optional[Token]:
        if self._index < len(self._tokens):
            return self._tokens[self._index]
        return None

    def peek(self, offset: int = 0) -> Optional[Token]:
        index = self._index + offset
        if index < len(self._tokens):
            return self._tokens[index]
        return None

    def advance(self) -> Optional[Token]:
        token = self.current()
        if token is not None:
            self._index += 1
        return token

    def is_at_end(self) -> bool:
        return self.current() is None

    def match_keyword(self, *values: str) -> bool:
        token = self.current()
        if token is None or token.kind != "identifier":
            return False
        if token.value.upper() in values:
            self.advance()
            return True
        return False

    def match_symbol(self, value: str) -> bool:
        token = self.current()
        if token is None or token.kind != "symbol" or token.value != value:
            return False
        self.advance()
        return True

    def consume(self) -> Optional[Token]:
        return self.advance()

    def skip_until(self, *values: str) -> None:
        while not self.is_at_end():
            token = self.current()
            if token is not None and token.kind == "identifier" and token.value.upper() in values:
                return
            self.advance()
