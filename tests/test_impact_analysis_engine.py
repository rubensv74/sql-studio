import unittest

from sqlstudio.impact_analysis import ImpactAnalysisEngine

class Edge:
    def __init__(self, source, target):
        self.source=source
        self.target=target

class Graph:
    def __init__(self):
        self.edges=[
            Edge("A","B"),
            Edge("B","C"),
            Edge("C","A"),
            Edge("B","D")
        ]

class TestImpactAnalysisEngine(unittest.TestCase):

    def test_analyze(self):
        result=ImpactAnalysisEngine().analyze(Graph(),"A")
        self.assertEqual(result.root_object,"A")
        self.assertIn("D", result.impacted_objects)
        self.assertEqual(len(result.impacted_objects),4)

if __name__=="__main__":
    unittest.main()
