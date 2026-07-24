from .models import ImpactResult, ImpactNode
class ImpactAnalysisEngine:
    def build_tree(self, root, impacted):
        return ImpactNode(root,[ImpactNode(x) for x in impacted if x!=root])
