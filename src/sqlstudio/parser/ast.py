from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class Token:
    kind: str
    value: str
    position: int


@dataclass(frozen=True)
class Parameter:
    name: str
    datatype: Optional[str] = None
    default_value: Optional[str] = None
    output: bool = False


@dataclass(frozen=True)
class Variable:
    name: str
    value: Optional[str] = None


@dataclass(frozen=True)
class Reference:
    name: str
    schema: Optional[str] = None
    database: Optional[str] = None
    kind: str = "reference"


@dataclass(frozen=True)
class SqlObject:
    name: str
    schema: Optional[str] = None
    object_type: str = "Script"
    parameters: List[Parameter] = field(default_factory=list)
    variables: List[Variable] = field(default_factory=list)
    references: List[Reference] = field(default_factory=list)
    temporary_tables: List[str] = field(default_factory=list)
    dynamic_sql: bool = False


@dataclass(frozen=True)
class SqlDocument:
    sql_text: str
    objects: List[SqlObject] = field(default_factory=list)
    tokens: List[Token] = field(default_factory=list)
