import numpy as np

def huber_residuals(y_true, y_pred, delta=1.0):
    r = y_true - y_pred
    m = np.abs(r) <= delta
    return np.where(m, 0.5*r**2, delta*(np.abs(r) - 0.5*delta))

def zscore_mask(y, z=3.0):
    mu, sd = np.mean(y), np.std(y) + 1e-12
    return np.abs((y - mu)/sd) < z
