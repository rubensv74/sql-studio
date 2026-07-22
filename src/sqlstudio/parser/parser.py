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
        current_object: SqlObject | None = None
        current_parameter: Parameter | None = None
        in_parameter_list = False

        for index, token in enumerate(tokens):
            if token.value in {"#", "##"}:
                temporary_tables.append(token.value)
                continue

            if token.kind != "identifier":
                if token.value == "(":
                    in_parameter_list = current_object is not None
                elif token.value == ")":
                    in_parameter_list = False
                    current_parameter = None
                continue

            value = token.value.upper()
            if value == "CREATE":
                object_type = self._find_object_type(tokens, index + 1)
                if object_type is None:
                    continue
                name = self._extract_name(tokens, index + 1)
                current_object = SqlObject(name=name or f"Unnamed{object_type}", schema=None, object_type=object_type)
                objects.append(current_object)
            elif value == "DECLARE" and index + 1 < len(tokens):
                variable_name = self._extract_name(tokens, index + 1)
                if variable_name and not variable_name.startswith("@"):
                    variables.append(Variable(name=variable_name))
            elif value == "SET" and index + 1 < len(tokens):
                variable_name = self._extract_name(tokens, index + 1)
                if variable_name and variable_name.startswith("@"):
                    variables.append(Variable(name=variable_name))
            elif value in {"EXEC", "EXECUTE"}:
                dynamic_sql = True
                references.append(Reference(name="EXEC", kind="call"))
            elif value == "SP_EXECUTESQL":
                dynamic_sql = True
                references.append(Reference(name="sp_executesql", kind="call"))
            elif value in {"FROM", "JOIN", "UPDATE", "INTO", "DELETE", "MERGE", "OPENQUERY", "OPENROWSET"}:
                ref_name = self._extract_name(tokens, index + 1)
                if ref_name:
                    if "." in ref_name:
                        parts = ref_name.split(".")
                        references.append(Reference(name=parts[-1], schema=parts[-2] if len(parts) > 1 else None, database=parts[0] if len(parts) > 2 else None))
                    else:
                        references.append(Reference(name=ref_name))
            elif in_parameter_list and token.value.startswith("@"):
                current_parameter = Parameter(name=token.value)
                parameters.append(current_parameter)
            elif in_parameter_list and current_parameter is not None and value in {"OUTPUT", "OUT"}:
                current_parameter = Parameter(name=current_parameter.name, output=True)
                parameters[-1] = current_parameter
            elif in_parameter_list and current_parameter is not None and value not in {"AS", "RETURNS"}:
                if current_parameter.datatype is None and value not in {"INT", "VARCHAR", "NVARCHAR", "BIT", "DATE", "DATETIME", "DECIMAL", "FLOAT", "CHAR", "TABLE"}:
                    if current_parameter.default_value is None:
                        current_parameter = Parameter(name=current_parameter.name, datatype=current_parameter.datatype, default_value=token.value, output=current_parameter.output)
                        parameters[-1] = current_parameter
                elif current_parameter.datatype is None:
                    current_parameter = Parameter(name=current_parameter.name, datatype=token.value, output=current_parameter.output)
                    parameters[-1] = current_parameter

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

    def _find_object_type(self, tokens: List[Token], start: int) -> str | None:
        index = start
        while index < len(tokens):
            token = tokens[index]
            if token.kind != "identifier":
                index += 1
                continue
            value = token.value.upper()
            if value in {"OR", "ALTER"}:
                index += 1
                continue
            if value == "PROCEDURE":
                return "Stored Procedure"
            if value == "VIEW":
                return "View"
            if value == "FUNCTION":
                return "Function"
            if value == "TRIGGER":
                return "Trigger"
            if value == "TABLE":
                return "Table"
            index += 1
        return None

    def _extract_name(self, tokens: List[Token], start: int) -> str | None:
        for index in range(start, len(tokens)):
            token = tokens[index]
            if token.kind != "identifier":
                continue
            return token.value
        return None
