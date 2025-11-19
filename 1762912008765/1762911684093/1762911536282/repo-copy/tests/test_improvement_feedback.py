import unittest
from Learning_System.Improvement_Generator import ImprovementGenerator
from Learning_System.Feedback_Analyzer import FeedbackAnalyzer


class TestImprovementAndFeedback(unittest.TestCase):
    def test_feedback_analyzer_compute_gaps_defaults(self):
        fa = FeedbackAnalyzer()
        gaps_report = fa.compute_gaps(0.5, {}, {'risk_level': 'unknown'})
        self.assertIn('gaps', gaps_report)
        self.assertIn('suggested_fusion_weights', gaps_report)

    def test_improvement_generator_no_area(self):
        ig = ImprovementGenerator()
        # Pass empty feedback; should still return a plan dict
        plan = ig.generate_targeted_improvements({})
        self.assertIsInstance(plan, dict)
        self.assertIn('fusion_weights', plan)


if __name__ == '__main__':
    unittest.main()
