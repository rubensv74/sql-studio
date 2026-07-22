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
            if char in "(),;":
                tokens.append(Token(kind="symbol", value=char, position=self.position))
                self.position += 1
                continue
            if char in "'\"":
                start = self.position
                self.position += 1
                while self.position < len(self.sql_text) and self.sql_text[self.position] != char:
                    self.position += 1
                if self.position < len(self.sql_text):
                    self.position += 1
                tokens.append(Token(kind="literal", value=self.sql_text[start:self.position], position=start))
                continue
            if char in "#@":
                start = self.position
                self.position += 1
                while self.position < len(self.sql_text) and (self.sql_text[self.position].isalnum() or self.sql_text[self.position] in "._"):
                    self.position += 1
                tokens.append(Token(kind="identifier", value=self.sql_text[start:self.position], position=start))
                continue
            if char.isalnum() or char in "._":
                start = self.position
                self.position += 1
                while self.position < len(self.sql_text) and (self.sql_text[self.position].isalnum() or self.sql_text[self.position] in "._"):
                    self.position += 1
                value = self.sql_text[start:self.position]
                parts = value.split('.')
                if len(parts) > 1:
                    for part in parts:
                        tokens.append(Token(kind="identifier", value=part, position=start))
                        start += len(part) + 1
                else:
                    tokens.append(Token(kind="identifier", value=value, position=start))
                continue
            tokens.append(Token(kind="operator", value=char, position=self.position))
            self.position += 1
        return tokens
