import unittest

from Integration_Layer.Planner_Agent import PlannerAgent
from Integration_Layer.integration_registry import IntegrationRegistry


class TestPlannerAgent(unittest.TestCase):
    def setUp(self):
        # Use a fresh registry and register the PlannerAgent factory so tests
        # exercise the same registry-based resolution used in production.
        self.registry = IntegrationRegistry()
        self.registry.register_factory('planner_agent', lambda: PlannerAgent())

    def test_plan_contains_mb_and_units_for_diff(self):
        agent = self.registry.resolve('planner_agent')
        p = agent.plan("حل نظام المعادلات التفاضلية")
        engines = [n["plan"]["engine"] for n in p]
        self.assertIn("Mathematical_Brain", engines)
        self.assertIn("Units_Validator", engines)

    def test_execute_returns_outputs(self):
        agent = self.registry.resolve('planner_agent')
        out = agent.execute("حل نظام المعادلات التفاضلية")
        self.assertIn("outputs", out)
        self.assertGreaterEqual(len(out["outputs"]), 1)


if __name__ == '__main__':
    unittest.main()
