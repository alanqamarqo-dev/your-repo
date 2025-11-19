"""Simple uncertainty estimator using bootstrap (and residual fallback).

API:
  estimate(model, X, n_boot=200, alpha=0.05, random_state=None, method='bootstrap')
Returns dict: { 'y_hat': ndarray, 'ci_low': ndarray, 'ci_high': ndarray, 'sigma': ndarray }
"""
from __future__ import annotations
import numpy as np
from typing import Callable, Optional


def estimate(model, X, n_boot: int = 200, alpha: float = 0.05, random_state: Optional[int] = None, method: str = 'bootstrap'):
    X = _ensure_2d(X)
    rng = np.random.RandomState(random_state)
    # Obtain point predictions
    try:
        y_hat = np.asarray(model.predict(X))
    except Exception:
        raise

    n = X.shape[0]
    if method == 'bootstrap' and n_boot > 0:
        preds = np.zeros((n_boot, n))
        for i in range(n_boot):
            ids = rng.choice(n, size=n, replace=True)
            try:
                # if model has refit capability, we expect model to accept arrays
                preds_i = np.asarray(model.predict(X[ids]))
            except Exception:
                # fallback: use y_hat on ids
                preds_i = y_hat[ids]
            # place predictions back into full length by using ids mapping
            # here we use simple approach: compute preds on full X using model trained on bootstrap is ideal,
            # but if we can't retrain, approximate by using predictions from sampled indices
            preds[i, :] = np.interp(np.arange(n), ids, preds_i)
        lower = np.percentile(preds, 100 * (alpha / 2.0), axis=0)
        upper = np.percentile(preds, 100 * (1 - alpha / 2.0), axis=0)
        sigma = (upper - lower) / 4.0  # approx
        return {'y_hat': y_hat, 'ci_low': lower, 'ci_high': upper, 'sigma': sigma}

    # fallback: use residual-based estimate if model has been fitted
    # try to estimate via residual standard deviation if possible
    try:
        # model may have been trained; we cannot access training y here — give a conservative sigma
        sigma = np.ones(n) * np.std(y_hat) * 0.5
        lower = y_hat - 1.96 * sigma
        upper = y_hat + 1.96 * sigma
        return {'y_hat': y_hat, 'ci_low': lower, 'ci_high': upper, 'sigma': sigma}
    except Exception:
        # ultimate fallback
        sigma = np.ones(n) * 1e-6
        return {'y_hat': y_hat, 'ci_low': y_hat - sigma, 'ci_high': y_hat + sigma, 'sigma': sigma}


def _ensure_2d(X):
    arr = np.asarray(X)
    if arr.ndim == 1:
        return arr.reshape(-1, 1)
    return arr


__all__ = ['estimate']
