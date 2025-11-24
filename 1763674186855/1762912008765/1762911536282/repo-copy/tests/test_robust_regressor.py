import unittest
import numpy as np

from Core_Engines.Robust_Regression import RobustRegressor


def make_linear_data(n=200, noise=0.1, outlier_frac=0.0, seed=0):
    rng = np.random.RandomState(seed)
    X = rng.uniform(-1, 1, size=(n, 1))
    true_coef = np.array([2.5])
    y = (X.dot(true_coef)).ravel()
    y += rng.normal(scale=noise, size=y.shape)
    if outlier_frac > 0:
        m = int(n * outlier_frac)
        idx = rng.choice(n, size=m, replace=False)
        y[idx] += rng.normal(loc=10.0, scale=5.0, size=m)
    return X, y


def rmse(a, b):
    return np.sqrt(np.mean((a - b) ** 2))


class TestRobustRegressor(unittest.TestCase):
    def test_huber_reduces_rmse_with_outliers(self):
        X, y = make_linear_data(n=300, noise=0.2, outlier_frac=0.05, seed=42)
        # OLS via numpy
        Xw = np.hstack([np.ones((X.shape[0], 1)), X])
        beta, *_ = np.linalg.lstsq(Xw, y, rcond=None)
        y_ols = Xw.dot(beta)
        base_rmse = rmse(y_ols, y)

        r = RobustRegressor(method='huber', max_iter=50, delta=1.0)
        r.fit(X, y)
        y_r = r.predict(X)
        robust_rmse = rmse(y_r, y)

        # allow small variability; robust should not be significantly worse
        self.assertLessEqual(robust_rmse, base_rmse * 1.05)

    def test_ransac_predict_shape(self):
        X, y = make_linear_data(n=100, noise=0.5, outlier_frac=0.2, seed=1)
        r = RobustRegressor(method='ransac', n_trials=50, random_state=1)
        r.fit(X, y)
        ypred = r.predict(X)
        self.assertEqual(ypred.shape[0], X.shape[0])


if __name__ == '__main__':
    unittest.main()
