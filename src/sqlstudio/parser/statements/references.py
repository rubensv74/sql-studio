from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from ..ast import Token
from ..context import ParserContext
from ..names import normalize_identifier, split_qualified_name
from .base import StatementParser


@dataclass(frozen=True)
class _Relation:
    name: str
    schema: str | None
    database: str | None


class ReferenceStatementParser(StatementParser):
    _RELATION_KEYWORDS = {"FROM", "JOIN", "USING", "INTO", "APPLY"}
    _ALIAS_BOUNDARIES = {
        "APPLY", "CROSS", "EXCEPT", "FULL", "GROUP", "HAVING", "INNER", "INTERSECT",
        "JOIN", "LEFT", "ON", "ORDER", "OUTER", "PIVOT", "RIGHT", "SET", "UNION",
        "UNPIVOT", "USING", "WHERE", "WHEN", "WITH",
    }
    _NON_OBJECT_SOURCES = {"OPENQUERY", "OPENROWSET"}

    def parse(self, statement_tokens: Sequence[Token], context: ParserContext) -> bool:
        if not statement_tokens:
            return False

        cte_names = self._collect_cte_names(statement_tokens)
        aliases: dict[str, _Relation] = {}
        relations: list[_Relation] = []

        for index, token in enumerate(statement_tokens):
            if token.kind != "identifier":
                continue
            keyword = token.value.upper()

            if keyword in self._RELATION_KEYWORDS:
                relation_index = self._relation_index(statement_tokens, index + 1)
                if relation_index is None:
                    continue
                relation = self._relation_from_token(statement_tokens[relation_index], cte_names)
                if relation is None:
                    continue
                relations.append(relation)
                alias = self._relation_alias(statement_tokens, relation_index + 1)
                if alias is not None:
                    aliases[normalize_identifier(alias)] = relation
                continue

            if keyword == "MERGE":
                relation_index = self._relation_index(statement_tokens, index + 1, skip_keywords={"INTO"})
                if relation_index is None:
                    continue
                relation = self._relation_from_token(statement_tokens[relation_index], cte_names)
                if relation is not None:
                    relations.append(relation)

        # UPDATE frequently targets an alias declared later in a FROM clause.
        # Resolve aliases only after the first pass has seen every FROM/JOIN.
        # MERGE action clauses use ``UPDATE SET`` without a separate target;
        # SET is therefore a boundary, not an object name.
        for index, token in enumerate(statement_tokens):
            if token.kind != "identifier" or token.value.upper() != "UPDATE":
                continue
            target_index = self._relation_index(statement_tokens, index + 1)
            if target_index is None:
                continue
            target = statement_tokens[target_index]
            if target.value.upper() == "SET":
                continue
            alias_relation = aliases.get(normalize_identifier(target.value))
            if alias_relation is not None:
                relations.append(alias_relation)
                continue
            relation = self._relation_from_token(target, cte_names)
            if relation is not None:
                relations.append(relation)

        for relation in relations:
            context.ensure_object()
            context.add_reference(
                relation.name,
                schema=relation.schema,
                database=relation.database,
            )
        return True

    def _relation_from_token(self, token: Token, cte_names: set[str]) -> _Relation | None:
        if token.kind != "identifier":
            return None
        normalized = normalize_identifier(token.value)
        if normalized in cte_names or normalized in {name.casefold() for name in self._NON_OBJECT_SOURCES}:
            return None
        if token.value.startswith(("#", "@")):
            return None
        name, schema, database = split_qualified_name(token.value)
        if name is None or name.startswith(("#", "@")):
            return None
        return _Relation(name=name, schema=schema, database=database)

    @staticmethod
    def _relation_index(
        tokens: Sequence[Token],
        start: int,
        *,
        skip_keywords: set[str] | None = None,
    ) -> int | None:
        skip = skip_keywords or set()
        index = start
        while index < len(tokens):
            token = tokens[index]
            if token.value == "(":
                return None
            if token.kind == "identifier" and token.value.upper() in skip:
                index += 1
                continue
            return index if token.kind == "identifier" else None
        return None

    def _relation_alias(self, tokens: Sequence[Token], start: int) -> str | None:
        index = start
        if index < len(tokens) and tokens[index].value == "(":
            index = self._after_balanced(tokens, index)
        if index >= len(tokens):
            return None
        if tokens[index].kind == "identifier" and tokens[index].value.upper() == "AS":
            index += 1
        if index >= len(tokens) or tokens[index].kind != "identifier":
            return None
        candidate = tokens[index]
        if candidate.value.upper() in self._ALIAS_BOUNDARIES or candidate.value.startswith(("@", "#")):
            return None
        return candidate.value

    def _collect_cte_names(self, tokens: Sequence[Token]) -> set[str]:
        names: set[str] = set()
        for index, token in enumerate(tokens):
            if token.kind != "identifier" or token.value.upper() != "WITH":
                continue
            cursor = index + 1
            if cursor >= len(tokens) or tokens[cursor].kind != "identifier":
                continue

            while cursor < len(tokens):
                candidate = tokens[cursor]
                if candidate.kind != "identifier":
                    break
                after_name = cursor + 1
                if after_name < len(tokens) and tokens[after_name].value == "(":
                    after_name = self._after_balanced(tokens, after_name)
                if (
                    after_name + 1 >= len(tokens)
                    or tokens[after_name].kind != "identifier"
                    or tokens[after_name].value.upper() != "AS"
                    or tokens[after_name + 1].value != "("
                ):
                    break

                names.add(normalize_identifier(candidate.value))
                after_body = self._after_balanced(tokens, after_name + 1)
                if after_body >= len(tokens) or tokens[after_body].value != ",":
                    break
                cursor = after_body + 1
        return names

    @staticmethod
    def _after_balanced(tokens: Sequence[Token], opening_index: int) -> int:
        depth = 0
        for index in range(opening_index, len(tokens)):
            if tokens[index].value == "(":
                depth += 1
            elif tokens[index].value == ")":
                depth -= 1
                if depth == 0:
                    return index + 1
        return len(tokens)
