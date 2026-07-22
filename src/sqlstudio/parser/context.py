from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence

from .ast import Parameter, Reference, SqlObject, Token, Variable
from .token_stream import TokenStream


@dataclass
class ParserContext:
    tokens: Sequence[Token]
    stream: TokenStream = field(init=False)
    objects: List[SqlObject] = field(default_factory=list)
    parameters: List[Parameter] = field(default_factory=list)
    variables: List[Variable] = field(default_factory=list)
    references: List[Reference] = field(default_factory=list)
    temporary_tables: List[str] = field(default_factory=list)
    dynamic_sql: bool = False
    current_object: Optional[SqlObject] = None
    current_parameter: Optional[Parameter] = None
    seen_variables: set[str] = field(default_factory=set)
    diagnostics: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.stream = TokenStream(list(self.tokens))

    def ensure_object(self) -> SqlObject:
        if self.current_object is None:
            object_name = "UnnamedScript"
            script_object = SqlObject(name=object_name, schema=None, object_type="Script")
            self.objects.append(script_object)
            self.current_object = script_object
        return self.current_object

    def add_object(self, obj: SqlObject) -> None:
        self.objects.append(obj)
        self.current_object = obj

    def add_parameter(self, parameter: Parameter) -> None:
        self.parameters.append(parameter)
        self.current_parameter = parameter

    def update_last_parameter(self, *, datatype: Optional[str] = None, default_value: Optional[str] = None, output: Optional[bool] = None) -> None:
        if not self.parameters:
            return
        last = self.parameters[-1]
        updated = Parameter(
            name=last.name,
            datatype=datatype if datatype is not None else last.datatype,
            default_value=default_value if default_value is not None else last.default_value,
            output=last.output if output is None else output,
        )
        self.parameters[-1] = updated
        self.current_parameter = updated

    def add_variable(self, name: str) -> None:
        if name and name not in self.seen_variables:
            self.variables.append(Variable(name=name))
            self.seen_variables.add(name)

    def add_reference(self, name: str, *, schema: Optional[str] = None, database: Optional[str] = None, kind: str = "reference") -> None:
        self.references.append(Reference(name=name, schema=schema, database=database, kind=kind))

    def add_temporary_table(self, name: str) -> None:
        if name and name not in self.temporary_tables:
            self.temporary_tables.append(name)

    def add_diagnostic(self, message: str) -> None:
        self.diagnostics.append(message)
