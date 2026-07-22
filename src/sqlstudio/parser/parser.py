from __future__ import annotations

from typing import List

from .ast import Parameter, Reference, SqlDocument, SqlObject, Token, Variable
from .tokenizer import SQLTokenizer


class SQLParser:
    def __init__(self) -> None:
        self._tokens: List[Token] = []

    def parse(self, sql_text: str) -> SqlDocument:
        if not sql_text or not sql_text.strip():
            return SqlDocument(sql_text=sql_text, objects=[])

        tokenizer = SQLTokenizer(sql_text)
        tokens = tokenizer.tokenize()
        self._tokens = tokens

        objects: List[SqlObject] = []
        parameters: List[Parameter] = []
        variables: List[Variable] = []
        references: List[Reference] = []
        temporary_tables: List[str] = []
        dynamic_sql = False

        for index, token in enumerate(tokens):
            if token.kind != "identifier":
                continue
            value = token.value.upper()
            if value == "CREATE":
                next_token = tokens[index + 1].value.upper() if index + 1 < len(tokens) else ""
                if next_token == "PROCEDURE":
                    name = self._extract_name(tokens, index + 2)
                    objects.append(SqlObject(name=name or "UnnamedProcedure", schema=None, object_type="Stored Procedure"))
                elif next_token == "VIEW":
                    name = self._extract_name(tokens, index + 2)
                    objects.append(SqlObject(name=name or "UnnamedView", schema=None, object_type="View"))
                elif next_token == "FUNCTION":
                    name = self._extract_name(tokens, index + 2)
                    objects.append(SqlObject(name=name or "UnnamedFunction", schema=None, object_type="Function"))
                elif next_token == "TRIGGER":
                    name = self._extract_name(tokens, index + 2)
                    objects.append(SqlObject(name=name or "UnnamedTrigger", schema=None, object_type="Trigger"))
                elif next_token == "TABLE":
                    name = self._extract_name(tokens, index + 2)
                    objects.append(SqlObject(name=name or "UnnamedTable", schema=None, object_type="Table"))
            elif value == "DECLARE":
                variable_name = self._extract_name(tokens, index + 1)
                if variable_name:
                    variables.append(Variable(name=variable_name))
            elif value == "SET":
                variable_name = self._extract_name(tokens, index + 1)
                if variable_name:
                    variables.append(Variable(name=variable_name))
            elif value == "EXEC" or value == "EXECUTE":
                dynamic_sql = True
                references.append(Reference(name="EXEC", kind="call"))
            elif value == "SP_EXECUTESQL":
                dynamic_sql = True
                references.append(Reference(name="sp_executesql", kind="call"))
            elif value == "SELECT" and index + 1 < len(tokens):
                next_value = tokens[index + 1].value.upper() if index + 1 < len(tokens) else ""
                if next_value == "*":
                    pass
            elif value == "FROM" or value == "JOIN" or value == "UPDATE" or value == "INTO" or value == "DELETE" or value == "MERGE" or value == "OPENQUERY" or value == "OPENROWSET":
                ref_name = self._extract_name(tokens, index + 1)
                if ref_name:
                    references.append(Reference(name=ref_name))

            if token.value == "#" or token.value == "##":
                temporary_tables.append(token.value)

        if objects:
            first_object = objects[0]
            object_with_details = SqlObject(
                name=first_object.name,
                schema=first_object.schema,
                object_type=first_object.object_type,
                parameters=parameters,
                variables=variables,
                references=references,
                temporary_tables=temporary_tables,
                dynamic_sql=dynamic_sql,
            )
            objects = [object_with_details]

        return SqlDocument(sql_text=sql_text, objects=objects, tokens=tokens)

    def _extract_name(self, tokens: List[Token], start: int) -> str | None:
        for index in range(start, len(tokens)):
            token = tokens[index]
            if token.kind != "identifier":
                continue
            return token.value
        return None
