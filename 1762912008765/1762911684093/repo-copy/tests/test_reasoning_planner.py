import unittest
from Core_Engines.Reasoning_Planner import ReasoningPlanner


class TestReasoningPlanner(unittest.TestCase):
    def test_plan_basic(self):
        rp = ReasoningPlanner()
        res = rp.plan('estimate fall time', context={'meta': {'len': 10}})
        self.assertIsInstance(res.get('steps'), list)
        self.assertGreaterEqual(len(res.get('steps') or []), 3)
        self.assertIn('justification', res)
        self.assertGreater(res.get('confidence', 0.0), 0.0)


if __name__ == '__main__':
    unittest.main()
