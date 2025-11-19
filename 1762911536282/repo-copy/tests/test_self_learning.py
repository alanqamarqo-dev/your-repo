import unittest
from Learning_System.Self_Learning_Module import SelfLearningModule, Hypothesis

class TestSelfLearning(unittest.TestCase):
    """نختبر توليد الفرضيات وملاءمة ثابت هوك."""

    def test_generate_hypotheses_nonempty(self):
        sl = SelfLearningModule()
        hyps = sl.generate_hypotheses()
        self.assertTrue(len(hyps) >= 2)
        names = {h.name for h in hyps}
        self.assertIn("hooke", names)
        self.assertIn("ohm", names)

    def test_fit_k_in_hooke(self):
        true_k = 3.5
        X = [{"x": x} for x in [0.0, 0.5, 1.0, 2.0, 3.0]]
        y = [true_k * xi["x"] for xi in X]

        sl = SelfLearningModule()
        hyp = [h for h in sl.generate_hypotheses("hooke") if h.name == "hooke"][0]
        fitted = sl.fit_params(hyp, X, y)

        self.assertIn("k", fitted.params)
        self.assertAlmostEqual(fitted.params["k"], true_k, places=4)

        mse = sl.evaluate_mse(fitted, X, y)
        self.assertLess(mse, 1e-10)

if __name__ == "__main__":
    unittest.main()
