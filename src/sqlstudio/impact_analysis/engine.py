from collections import deque
from .models import ImpactResult

class ImpactAnalysisEngine:
    def analyze(self, graph, root_object: str):
        impacted=[]
        visited=set()
        q=deque([root_object])
        while q:
            current=q.popleft()
            if current in visited:
                continue
            visited.add(current)
            impacted.append(current)
            for edge in getattr(graph, 'edges', []):
                if getattr(edge, 'source', None)==current:
                    q.append(getattr(edge, 'target'))
        return ImpactResult(root_object=root_object, impacted_objects=impacted)
