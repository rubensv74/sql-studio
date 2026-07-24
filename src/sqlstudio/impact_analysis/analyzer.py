from .engine import ImpactAnalysisEngine
from sqlstudio.dependencies import DependencyAnalyzer

class ImpactAnalyzer:
    def __init__(self):
        self._dependency=DependencyAnalyzer()
        self._engine=ImpactAnalysisEngine()

    def analyze(self, sql_text:str, root_object:str):
        graph=self._dependency.analyze(sql_text)
        return self._engine.analyze(graph, root_object)

    def analyze_many(self, sql_texts, root_object:str):
        graph=self._dependency.analyze_many(sql_texts)
        return self._engine.analyze(graph, root_object)
