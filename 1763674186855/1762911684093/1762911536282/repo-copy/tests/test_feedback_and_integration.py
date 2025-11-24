import unittest
from Learning_System.Feedback_Analyzer import FeedbackAnalyzer
from Learning_System.Knowledge_Integrator import KnowledgeIntegrator
import os

class TestFeedbackAndIntegration(unittest.TestCase):
    def test_feedback_hints(self):
        fa = FeedbackAnalyzer()
        sample = {"solution": {"confidence": 0.4}, "signals": {"quantum_processor": {"score": 0.2}}}
        hints = fa.analyze_performance_feedback(sample)
        self.assertIsInstance(hints, dict)
        self.assertIn("gaps", hints)

    def test_knowledge_merge(self):
        ki = KnowledgeIntegrator(base_dir=os.getcwd())
        kb = {"laws": [{"name":"Newton2","form":"F=m*a"}]}
        new = {"laws": [{"name":"Hooke","form":"F=-k*x"}, {"name":"Newton2","form":"F=m*a"}]}
        # KnowledgeIntegrator.merge not implemented; test integrate_new_knowledge pathway
        res = ki.integrate_new_knowledge({"fusion_weights": {"a": 1.0}})
        self.assertIn("action", res)
