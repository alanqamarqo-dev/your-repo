"""Simple, self-contained robust regression utilities.

Provides RobustRegressor supporting 'huber' (IRLS) and 'ransac' modes
using only numpy/scipy so it works in CI without scikit-learn.

API:
    r = RobustRegressor(method='huber')
    r.fit(X, y)
    y_pred = r.predict(X)
    rmse = r.score(X, y)
"""
from __future__ import annotations
from typing import Optional
import warnings

import numpy as np
from scipy import linalg


class RobustRegressor:
    def __init__(self, method: str = 'huber', max_iter: int = 100, delta: float = 1.0, n_trials: int = 100, random_state: Optional[int] = None):
        self.method = method
        self.max_iter = int(max_iter)
        self.delta = float(delta)
        self.n_trials = int(n_trials)
        self.random_state = random_state
        self.coef_ = None
        self.intercept_ = 0.0

    def fit(self, X, y):
        X = self._ensure_2d(X)
        y = np.asarray(y).ravel()
        if self.method == 'huber':
            self._irls_huber(X, y, delta=self.delta, max_iter=self.max_iter)
            return self
        if self.method == 'ransac':
            self._simple_ransac(X, y, n_trials=self.n_trials)
            return self
        raise ValueError(f"Unknown method: {self.method}")

    def predict(self, X):
        X = self._ensure_2d(X)
        if self.coef_ is None:
            raise ValueError('Model is not fitted')
        return X.dot(self.coef_) + self.intercept_

    def score(self, X, y):
        y = np.asarray(y).ravel()
        y_pred = self.predict(X)
        return float(np.sqrt(np.mean((y - y_pred) ** 2)))

    def _ensure_2d(self, X):
        arr = np.asarray(X)
        if arr.ndim == 1:
            return arr.reshape(-1, 1)
        return arr

    def _irls_huber(self, X, y, delta=1.0, max_iter=100, tol=1e-6):
        # Iteratively Reweighted Least Squares for Huber loss
        n, p = X.shape
        Xw = np.hstack([np.ones((n, 1)), X])
        beta = np.zeros(p + 1)
        for _ in range(max_iter):
            residuals = y - Xw.dot(beta)
            abs_r = np.abs(residuals)
            # Huber weights
            w = np.where(abs_r <= delta, 1.0, delta / abs_r)
            W = np.sqrt(w)
            Xrw = Xw * W[:, None]
            yrw = y * W
            try:
                beta_new, *_ = linalg.lstsq(Xrw, yrw) # type: ignore
            except Exception:
                warnings.warn('IRLS lstsq failed; using unweighted lstsq')
                beta_new, *_ = linalg.lstsq(Xw, y) # type: ignore
            if np.linalg.norm(beta_new - beta) < tol:
                beta = beta_new
                break
            beta = beta_new
        self.intercept_ = float(beta[0])
        self.coef_ = np.asarray(beta[1:])

    def _simple_ransac(self, X, y, n_trials=100, min_samples=None, threshold=None):
        n, p = X.shape
        if min_samples is None:
            min_samples = max(2, p + 1)
        if threshold is None:
            threshold = 2.5 * np.std(y)
        best_inliers = np.array([], dtype=int)
        rng = np.random.RandomState(self.random_state)
        Xw = np.hstack([np.ones((n, 1)), X])
        best_beta = None
        for _ in range(n_trials):
            ids = rng.choice(n, size=min_samples, replace=False)
            try:
                beta, *_ = linalg.lstsq(Xw[ids], y[ids]) # type: ignore
            except Exception:
                continue
            resid = np.abs(y - Xw.dot(beta))
            inliers = np.where(resid <= threshold)[0]
            if inliers.size > best_inliers.size:
                best_inliers = inliers
                best_beta = beta
        if best_beta is None:
            beta, *_ = linalg.lstsq(Xw, y) # type: ignore
            best_beta = beta
        else:
            # refine using all inliers
            try:
                beta, *_ = linalg.lstsq(Xw[best_inliers], y[best_inliers]) # type: ignore
                best_beta = beta
            except Exception:
                pass
        self.intercept_ = float(best_beta[0])
        self.coef_ = np.asarray(best_beta[1:])


__all__ = ['RobustRegressor']

# Backwards-compatible alias expected by ENGINE_SPECS
RobustRegression = RobustRegressor  # type: ignore


def create_engine(config: dict | None = None):
    """Return a small engine-like object exposing process_task to satisfy bootstrap/tests."""
    class _EngineWrapper:
        def __init__(self):
            self.name = 'Robust_Regression'
            self._model = RobustRegressor()

        def process_task(self, payload: dict) -> dict:
            try:
                action = payload.get('action')
                if action == 'fit':
                    X = payload.get('X') or []
                    y = payload.get('y') or []
                    self._model.fit(X, y)
                    return {'ok': True, 'fitted': True}
                if action == 'predict':
                    X = payload.get('X') or []
                    pred = self._model.predict(X)
                    return {'ok': True, 'pred': pred.tolist() if hasattr(pred, 'tolist') else list(pred)}
                return {'ok': True, 'msg': 'noop'}
            except Exception as e:
                return {'ok': False, 'error': str(e)}

    return _EngineWrapper()
