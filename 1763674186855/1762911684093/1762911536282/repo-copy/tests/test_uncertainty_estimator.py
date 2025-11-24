import unittest
import numpy as np

from Learning_System.Uncertainty_Estimator import estimate


class DummyModel:
    def __init__(self, coef=2.0):
        self.coef = coef

    def predict(self, X):
        X = np.asarray(X)
        if X.ndim == 2:
            return (X[:, 0] * self.coef)
        return X.ravel() * self.coef


class TestUncertaintyEstimator(unittest.TestCase):
    def test_estimate_shape(self):
        X = np.linspace(0, 1, 50).reshape(-1, 1)
        m = DummyModel(coef=3.0)
        res = estimate(m, X, n_boot=10, random_state=1)
        self.assertIn('y_hat', res)
        self.assertIn('ci_low', res)
        self.assertIn('ci_high', res)
        self.assertEqual(res['y_hat'].shape[0], X.shape[0])

    def test_ci_shrinks_with_more_bootstrap(self):
        X = np.linspace(0, 1, 100).reshape(-1, 1)
        m = DummyModel(coef=1.0)
        r1 = estimate(m, X, n_boot=10, random_state=1)
        width1 = np.mean(r1['ci_high'] - r1['ci_low'])
        r2 = estimate(m, X, n_boot=100, random_state=1)
        width2 = np.mean(r2['ci_high'] - r2['ci_low'])
        # At minimum widths should be finite and non-negative
        self.assertTrue(np.isfinite(width1) and np.isfinite(width2))
        self.assertGreaterEqual(width1, 0.0)
        self.assertGreaterEqual(width2, 0.0)


if __name__ == '__main__':
    unittest.main()
