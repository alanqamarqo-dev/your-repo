import unittest
import random
from Learning_System.Law_Learner import fit_single_coeff_linear


class TestLawLearner(unittest.TestCase):
    def test_fit_k_in_hooke(self):
        true_k = 12.5
        xs = [i*0.1 for i in range(1, 101)]
        ys = [true_k*x + random.gauss(0, 0.05) for x in xs]
        res = fit_single_coeff_linear("F = k*x", "F", "x", {"F": ys, "x": xs})
        self.assertAlmostEqual(res["coef"], true_k, delta=0.2)
        self.assertLess(res["rmse"], 0.2)
        self.assertGreater(res["confidence"], 0.6)


if __name__ == "__main__":
    unittest.main()
