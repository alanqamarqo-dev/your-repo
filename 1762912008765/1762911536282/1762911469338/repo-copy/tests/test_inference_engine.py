import unittest
from Learning_System.Inference_Engine import InferenceEngine

class TestInferenceEngine(unittest.TestCase):
    def setUp(self):
        self.ie = InferenceEngine()

    def test_rc_tau_derivation(self):
        p = self.ie.get_pattern("rc_step")
        a = float(p["fit"]["a"])
        out = self.ie.predict("rc_step", 0.0)
        self.assertIn("tau", out["derived"])
        self.assertAlmostEqual(out["derived"]["tau"], -1.0/a, places=6)

    def test_ohm_linear_predict_consistency(self):
        p = self.ie.get_pattern("ohm")
        a = float(p["fit"]["a"]); b = float(p["fit"]["b"])
        x = 0.12
        out = self.ie.predict("ohm", x)
        self.assertAlmostEqual(out["y"], a*x + b, places=9)

    def test_poly2_vector(self):
        out = self.ie.predict("poly2", [0.0, 1.0, 2.0])
        self.assertIn("y_list", out)
        self.assertEqual(len(out["y_list"]), 3)

if __name__ == "__main__":
    unittest.main()
