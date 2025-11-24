import unittest
from Integration_Layer.Task_Orchestrator import TaskOrchestrator
from Integration_Layer.Output_Formatter import OutputFormatter

class TestTaskOrchestratorPaths(unittest.TestCase):
    def setUp(self):
        self.orch = TaskOrchestrator()
        self.fmt = OutputFormatter()

    def test_route_differential_system(self):
        task = "حل نظام المعادلات التفاضلية"
        result = self.orch.process_task(task)
        self.assertIsInstance(result, dict)
        self.assertIn("solution", result)
        self.assertIn("confidence", result)
        formatted = self.fmt.format_output(result)
        self.assertIsInstance(formatted, dict)
        self.assertTrue(len(formatted.get('result', {})) > 0)

    def test_unknown_task_fails_gracefully(self):
        task = "مهمة غير معروفة 123"
        result = self.orch.process_task(task)
        self.assertIsInstance(result, dict)
        self.assertTrue(any(k in result for k in ("error","reason","status")))

    def test_pcx_rpl_hooks(self):
        # basic smoke test: plan generation and PCX annotation
        plan = self.orch.plan_for_goal('verify sensor pipeline', {'user': 'bob', 'task': 'verify'})
        self.assertIsInstance(plan, dict)
        self.assertIn('steps', plan)
        self.assertGreaterEqual(len(plan.get('steps', [])), 1)
