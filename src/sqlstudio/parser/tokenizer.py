from __future__ import annotations

from typing import List

from .ast import Token


class SQLTokenizer:
    def __init__(self, sql_text: str):
        self.sql_text = sql_text
        self.position = 0

    def tokenize(self) -> List[Token]:
        tokens: List[Token] = []
        while self.position < len(self.sql_text):
            char = self.sql_text[self.position]
            if char.isspace():
                self.position += 1
                continue
            if char == "-" and self.position + 1 < len(self.sql_text) and self.sql_text[self.position + 1] == "-":
                self.position += 2
                while self.position < len(self.sql_text) and self.sql_text[self.position] != "\n":
                    self.position += 1
                continue
            if char == "/" and self.position + 1 < len(self.sql_text) and self.sql_text[self.position + 1] == "*":
                self.position += 2
                while self.position + 1 < len(self.sql_text) and not (self.sql_text[self.position] == "*" and self.sql_text[self.position + 1] == "/"):
                    self.position += 1
                self.position += 2 if self.position + 1 < len(self.sql_text) else 0
                continue
            if char in "(),;":
                tokens.append(Token(kind="symbol", value=char, position=self.position))
                self.position += 1
                continue
            if char in "'\"":
                tokens.append(self._read_quoted_literal(char))
                continue
            if char in "#@":
                start = self.position
                self.position += 1
                while self.position < len(self.sql_text) and (self.sql_text[self.position].isalnum() or self.sql_text[self.position] in "._$"):
                    self.position += 1
                tokens.append(Token(kind="identifier", value=self.sql_text[start:self.position], position=start))
                continue
            if self._can_start_identifier_segment(char):
                start = self.position
                value = self._read_qualified_identifier()
                tokens.append(Token(kind="identifier", value=value, position=start))
                continue
            tokens.append(Token(kind="operator", value=char, position=self.position))
            self.position += 1
        return tokens

    def _read_quoted_literal(self, quote: str) -> Token:
        start = self.position
        self.position += 1
        while self.position < len(self.sql_text):
            if self.sql_text[self.position] != quote:
                self.position += 1
                continue
            if self.position + 1 < len(self.sql_text) and self.sql_text[self.position + 1] == quote:
                self.position += 2
                continue
            self.position += 1
            break
        return Token(kind="literal", value=self.sql_text[start:self.position], position=start)

    def _read_qualified_identifier(self) -> str:
        parts: list[str] = []
        while self.position < len(self.sql_text):
            if self.sql_text[self.position] == "[":
                segment = self._read_bracketed_segment()
            else:
                segment = self._read_simple_segment()
            if not segment:
                break
            parts.append(segment)

            if self.position >= len(self.sql_text) or self.sql_text[self.position] != ".":
                break
            dot_position = self.position
            self.position += 1
            if self.position >= len(self.sql_text) or not self._can_start_identifier_segment(self.sql_text[self.position]):
                self.position = dot_position
                break

        return ".".join(parts)

    def _read_simple_segment(self) -> str:
        start = self.position
        while self.position < len(self.sql_text) and (
            self.sql_text[self.position].isalnum() or self.sql_text[self.position] in "_$"
        ):
            self.position += 1
        return self.sql_text[start:self.position]

    def _read_bracketed_segment(self) -> str:
        start = self.position
        self.position += 1
        while self.position < len(self.sql_text):
            if self.sql_text[self.position] != "]":
                self.position += 1
                continue
            if self.position + 1 < len(self.sql_text) and self.sql_text[self.position + 1] == "]":
                self.position += 2
                continue
            self.position += 1
            break
        return self.sql_text[start:self.position]

    @staticmethod
    def _can_start_identifier_segment(char: str) -> bool:
        return char == "[" or char.isalnum() or char in "_$"
