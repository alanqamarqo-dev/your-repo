import unittest
from Core_Engines.Mathematical_Brain import MathematicalBrain

class TestMathematicalBrainBranches(unittest.TestCase):
    def setUp(self):
        self.mb = MathematicalBrain()

    def test_parse_bad_input(self):
        with self.assertRaises(Exception):
            self.mb.parse_equation(None)  # type: ignore

    def test_symbolic_solution_verification(self):
        eq = "y'' + 0*y' + 0*y = 0"
        sol = self.mb.process_task('solve differential')
        self.assertIn("result", sol)
        # If process_task returns verification structure for differential, ensure residual small
        res = sol.get('result')
        if isinstance(res, dict) and isinstance(res.get('verification'), dict):
            self.assertLessEqual(res['verification'].get('residual_norm', 1.0), 1e-3)
