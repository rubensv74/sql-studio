from dataclasses import dataclass, field
from typing import List

@dataclass
class ImpactResult:
    root_object: str
    impacted_objects: List[str] = field(default_factory=list)
