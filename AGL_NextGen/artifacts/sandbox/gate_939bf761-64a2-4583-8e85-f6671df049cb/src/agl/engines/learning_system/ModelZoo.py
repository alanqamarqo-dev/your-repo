from dataclasses import dataclass
from typing import Callable, Dict, Tuple, List
import math
import json

@dataclass
class FitResult:
    a: float
    b: float
    rmse: float
    n: int
    confidence: float

def rmse(y_true, y_pred):
    n = len(y_true)
    e2 = sum((yt - yp)**2 for yt, yp in zip(y_true, y_pred))
    return (e2 / max(1, n)) ** 0.5

def _conf_from_rmse(rmse_val: float, span: float) -> float:
    # تحويل RMSE إلى درجة ثقة بسيطة (كلما قلّ كان أفضل)
    if span <= 1e-12:  # حماية
        return 0.5
    score = max(0.0, 1.0 - (rmse_val / (span + 1e-9)))
    # ضغط خفيف
    return max(0.0, min(1.0, 0.2 + 0.8*score))

def fit_linear(x, y):
    # نموذج: y = k*x
    n = len(x)
    denom = sum(xi*xi for xi in x)
    k = (sum(xi*yi for xi, yi in zip(x, y)) / denom) if denom else 0.0
    yhat = [k*xi for xi in x]
    r = rmse(y, yhat)
    conf = _conf_from_rmse(r, (max(y)-min(y)) if y else 1.0)
    return FitResult(a=k, b=0.0, rmse=r, n=n, confidence=conf)

def fit_linear_bias(x, y):
    # نموذج: y = k*x + b
    n = len(x)
    sx = sum(x); sy = sum(y)
    sxx = sum(xi*xi for xi in x)
    sxy = sum(xi*yi for xi, yi in zip(x,y))
    denom = n*sxx - sx*sx
    if abs(denom) < 1e-12:
        return FitResult(a=0.0, b=0.0, rmse=1e9, n=n, confidence=0.0)
    k = (n*sxy - sx*sy)/denom
    b = (sy - k*sx)/n
    yhat = [k*xi + b for xi in x]
    r = rmse(y, yhat)
    conf = _conf_from_rmse(r, (max(y)-min(y)) if y else 1.0)
    return FitResult(a=k, b=b, rmse=r, n=n, confidence=conf)

def fit_poly2(x, y):
    # نموذج: y = a*x^2 + b*x (نبقيه بسيطًا بالتدرّج)
    # نبني مصفوفة طبيعية 2x2: [sum(x^4) sum(x^3); sum(x^3) sum(x^2)] * [a,b] = [sum(yx^2), sum(yx)]
    s2 = sum(xi*xi for xi in x)
    s3 = sum((xi**3) for xi in x)
    s4 = sum((xi**4) for xi in x)
    yx = sum(yi*xi for xi, yi in zip(x,y))
    yx2 = sum(yi*(xi**2) for xi, yi in zip(x,y))
    denom = s4*s2 - s3*s3
    if abs(denom) < 1e-12:
        return FitResult(a=0.0, b=0.0, rmse=1e9, n=len(x), confidence=0.0)
    a = (yx2*s2 - yx*s3)/denom
    b = (yx*s4 - yx2*s3)/denom
    yhat = [a*(xi**2) + b*xi for xi in x]
    r = rmse(y, yhat)
    conf = _conf_from_rmse(r, (max(y)-min(y)) if y else 1.0)
    return FitResult(a=a, b=b, rmse=r, n=len(x), confidence=conf)

def fit_exp1(t, y):
    """
    نموذج RC تقريبي: y = a + b*(1 - exp(-t/tau))
    نجرب tau على شبكة بسيطة ثم نلائم a,b بخطية (على شكل y = c + d*exp(-t/tau))
    """
    if not t:
        return FitResult(a=0.0, b=0.0, rmse=1e9, n=0, confidence=0.0)
    span = (max(y)-min(y)) if y else 1.0
    # شبكة tau بدائية
    tpos = [ti for ti in t if ti > 0]
    tmax = max(tpos) if tpos else 1.0
    candidates_tau = [0.1*tmax, 0.2*tmax, 0.5*tmax, 1.0*tmax, 2.0*tmax, 5.0*tmax]
    best = None
    for tau in candidates_tau:
        z = [math.exp(-ti/tau) for ti in t]
        # y ≈ a + b*(1 - exp(-t/tau)) = (a+b) + (-b)*exp(-t/tau) = c + d*z
        # خطية في c,d
        n = len(t)
        sz = sum(z); sy = sum(y)
        szz = sum(zi*zi for zi in z)
        szy = sum(zi*yi for zi,yi in zip(z,y))
        denom = n*szz - sz*sz
        if abs(denom) < 1e-12:
            continue
        c = (szz*sy - sz*szy)/denom
        d = (n*szy - sz*sy)/denom
        # استرجاع a,b: c = a+b, d = -b  =>  b = -d, a = c - b = c + d
        b = -d
        a = c + d
        yhat = [a + b*(1.0 - math.exp(-ti/tau)) for ti in t]
        r = rmse(y, yhat)
        conf = _conf_from_rmse(r, span)
        item = (r, a, b, tau, conf)
        if (best is None) or (r < best[0]):
            best = item
    if best is None:
        return FitResult(a=0.0, b=0.0, rmse=1e9, n=len(t), confidence=0.0)
    r, a, b, tau, conf = best
    # نُخزّن tau داخل b بشكل وصفي؟ سنعيده ضمن ميتاداتا عند الحاجة عبر الخارج
    return FitResult(a=a, b=b, rmse=r, n=len(t), confidence=conf)

# فهرس النماذج
MODEL_REGISTRY: Dict[str, Callable] = {
    "kx": fit_linear,           # y = k*x
    "k*x": fit_linear,          # alias
    "k*x + b": fit_linear_bias, # y = k*x + b
    "poly2": fit_poly2,         # y = a*x^2 + b*x
    "a*x**2": fit_poly2,        # alias
    "exp1": fit_exp1            # y = a + b*(1 - exp(-t/tau))
}

def evaluate_candidates(x: List[float], y: List[float], candidates: List[str]) -> List[Dict]:
    span = (max(y)-min(y)) if y else 1.0
    out = []
    for name in candidates:
        fn = MODEL_REGISTRY.get(name)
        if not fn:
            continue
        res = fn(x, y)
        out.append({
            "candidate": name,
            "fit": {
                "a": res.a,
                "b": res.b,
                "rmse": res.rmse,
                "n": res.n,
                "confidence": res.confidence
            }
        })
    # ترتيب حسب RMSE
    out.sort(key=lambda r: r["fit"]["rmse"])
    return out
