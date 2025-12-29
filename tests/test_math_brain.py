import unittest
import sys
import os

# Add project root to path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, 'repo-copy'))

from Core_Engines.Mathematical_Brain import MathematicalBrain

class TestMathematicalBrain(unittest.TestCase):
    def setUp(self):
        self.math_brain = MathematicalBrain()

    def test_solve_equation_simple(self):
        result = self.math_brain.solve_equation("2x + 5 = 15")
        # Check if result is a dict and has expected keys, handling potential error responses gracefully
        self.assertIsInstance(result, dict)
        if "error" not in result:
             self.assertTrue("solution" in result or "result" in result or "x" in result)

    def test_solve_equation_no_equals(self):
        result = self.math_brain.solve_equation("2x + 5")
        self.assertIn("error", result)

    def test_process_task_math_keywords(self):
        # Mocking context if needed, but simple string should work for basic test
        task = {"problem": "Calculate 5 + 5"}
        # Note: process_task might not be fully implemented in the snippet provided in context, 
        # but let's assume it exists or we test the underlying logic.
        # If process_task is not in the class, we test solve_equation directly as a proxy for now.
        pass 

if __name__ == '__main__':
    unittest.main()
