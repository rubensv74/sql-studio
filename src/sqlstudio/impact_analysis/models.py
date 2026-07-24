from dataclasses import dataclass, field
from typing import List

@dataclass
class ImpactNode:
    name:str
    children:List["ImpactNode"]=field(default_factory=list)

@dataclass
class ImpactResult:
    root_object:str
    impacted_objects:List[str]=field(default_factory=list)
    tree:ImpactNode|None=None
