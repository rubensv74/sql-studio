from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence

from .ast import Parameter, Reference, SqlObject, Token, Variable
from .token_stream import TokenStream


@dataclass
class ParserContext:
    """Mutable parser state with evidence owned by one active SQL object.

    ``SqlObject`` remains the public immutable AST model. The context keeps the
    active object's mutable evidence separately and materializes a complete
    ``SqlObject`` whenever the scope ends. This prevents references, parameters,
    variables, temporary tables and dynamic-SQL evidence from leaking between
    multiple durable definitions in the same source file.
    """

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
    seen_references: set[tuple[str, str, str, str]] = field(default_factory=set)
    diagnostics: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.stream = TokenStream(list(self.tokens))

    def ensure_object(self) -> SqlObject:
        """Return the active object, creating a script scope when necessary."""

        if self.current_object is None:
            self.current_object = SqlObject(
                name="UnnamedScript",
                schema=None,
                object_type="Script",
            )
        return self.current_object

    def add_object(self, obj: SqlObject) -> None:
        """Start a new durable-object scope and close the previous scope."""

        self.finalize_current_object()
        self.current_object = obj

    def finalize_current_object(self) -> None:
        """Materialize the active scope into the immutable public AST."""

        if self.current_object is None:
            self._reset_scope_evidence()
            return

        current = self.current_object
        self.objects.append(
            SqlObject(
                name=current.name,
                schema=current.schema,
                object_type=current.object_type,
                parameters=list(self.parameters),
                variables=list(self.variables),
                references=list(self.references),
                temporary_tables=list(self.temporary_tables),
                dynamic_sql=self.dynamic_sql,
            )
        )
        self.current_object = None
        self._reset_scope_evidence()

    def end_batch(self) -> None:
        """Close object ownership at a client batch boundary such as ``GO``."""

        self.finalize_current_object()

    def add_parameter(self, parameter: Parameter) -> None:
        self.ensure_object()
        self.parameters.append(parameter)
        self.current_parameter = parameter

    def update_last_parameter(
        self,
        *,
        datatype: Optional[str] = None,
        default_value: Optional[str] = None,
        output: Optional[bool] = None,
    ) -> None:
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
        if not name:
            return

        normalized = name.casefold()
        if any(parameter.name.casefold() == normalized for parameter in self.parameters):
            return
        if normalized in self.seen_variables:
            return

        self.ensure_object()
        self.variables.append(Variable(name=name))
        self.seen_variables.add(normalized)

    def add_reference(
        self,
        name: str,
        *,
        schema: Optional[str] = None,
        database: Optional[str] = None,
        kind: str = "reference",
    ) -> None:
        key = (
            (database or "").strip().casefold(),
            (schema or "").strip().casefold(),
            name.strip().casefold(),
            kind.strip().casefold(),
        )
        if not name.strip() or key in self.seen_references:
            return
        self.ensure_object()
        self.seen_references.add(key)
        self.references.append(
            Reference(name=name, schema=schema, database=database, kind=kind)
        )

    def add_temporary_table(self, name: str) -> None:
        if not name:
            return
        self.ensure_object()
        if name not in self.temporary_tables:
            self.temporary_tables.append(name)
        if name.startswith("#") and "#" not in self.temporary_tables:
            self.temporary_tables.append("#")

    def mark_dynamic_sql(self) -> None:
        self.ensure_object()
        self.dynamic_sql = True

    def add_diagnostic(self, message: str) -> None:
        self.diagnostics.append(message)

    def _reset_scope_evidence(self) -> None:
        self.parameters = []
        self.variables = []
        self.references = []
        self.temporary_tables = []
        self.dynamic_sql = False
        self.current_parameter = None
        self.seen_variables = set()
        self.seen_references = set()
