import unittest
from Integration_Layer.Task_Orchestrator import TaskOrchestrator

class TestOrchestratorInference(unittest.TestCase):
    def setUp(self):
        self.o = TaskOrchestrator()

    def test_predict_ohm(self):
        out = self.o.route("predict", {"base":"ohm", "x": 0.25})
        self.assertTrue(out.get("ok"))
        self.assertIn("result", out)

    def test_derive_rc_tau(self):
        out = self.o.route("derive", {"base":"rc_step"})
        self.assertTrue(out.get("ok"))
        self.assertIn("tau", out.get("derived", {}))

if __name__ == "__main__":
    unittest.main()
