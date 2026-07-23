from dataclasses import dataclass, field
from typing import Set

@dataclass
class DependencyNode:
    name:str
    kind:str
    depends_on:Set[str]=field(default_factory=set)
