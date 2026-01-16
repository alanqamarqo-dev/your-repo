from __future__ import annotations
import io, json, math, re, os
from typing import Any, Dict, List, Union

try:
    from agl.engines.learning_system.Uncertainty_Estimator import estimate as estimate_uncertainty
except Exception:
    estimate_uncertainty = None

Number = Union[int, float]

MIN_KB = {
    "version": "G.min",
    "updated_at": "auto",
    "patterns": [
        {"base": "ohm",   "winner": "ohm",   "fit": {"a": 10.0, "b": 0.0, "rmse": 0.0}},
        {"base": "poly2", "winner": "poly2", "fit": {"a": 1.0,  "b": 0.0, "rmse": 0.0}},
        {"base": "rc_step", "winner": "exp1", "fit": {"a": -0.02, "b": 1.0, "rmse": 0.0}},
        {"base": "exp1",  "winner": "exp1",  "fit": {"a": 0.1,  "b": 0.0, "rmse": 0.0}},
    ],
}


def _read_json_utf8(path: str):
    with io.open(path, 'r', encoding='utf-8-sig') as f:
        return json.load(f)


class InferenceEngine:
    def __init__(self, kb_path: str = "Knowledge_Base/Learned_Patterns.json"):
        self.kb_path = kb_path
        self.kb = self._load_kb(kb_path)
        # store for optional models used by uncertainty estimator
        self.model_store: Dict[str, Any] = {}
        try:
            from agl.engines.learning_system.Uncertainty_Estimator import estimate as estimate_uncertainty
        except Exception:
            estimate_uncertainty = None

    def _load_kb(self, path: str) -> Dict[str, Any]:
        # Try multiple candidate KB sources, support env override AGL_KB,
        # read UTF-8 safely, and fall back to MIN_KB when missing/corrupt.
        env_kb = os.environ.get("AGL_KB")
        candidates = [env_kb] if env_kb else []
        candidates += [path or "Knowledge_Base/Learned_Patterns.json",
                       "Knowledge_Base/Learned_Patterns.lock.json",
                       "Knowledge_Base/Learned_Patterns.json.new"]

        data = None
        for p in candidates:
            if not p:
                continue
            try:
                if os.path.exists(p):
                    data = _read_json_utf8(p)
                    # ensure dict
                    if isinstance(data, dict):
                        break
            except Exception:
                # try next candidate
                data = None

        # If nothing found or not a dict, return MIN_KB copy
        if not data or not isinstance(data, dict):
            return dict(MIN_KB)

        pats = data.get("patterns")
        if not isinstance(pats, list) or len(pats) == 0:
            # merge with minimum
            out = {"version": data.get("version", MIN_KB.get("version")),
                   "updated_at": data.get("updated_at", "auto"),
                   "patterns": list(MIN_KB["patterns"])}
            return out

        return data

    def get_pattern(self, base: str) -> Dict[str, Any]:
        pats = [p for p in self.kb["patterns"] if p.get("base") == base]
        if not pats:
            raise ValueError(f"No pattern found for base={base}")
        pats_sorted = sorted(pats, key=lambda p: float(p.get("fit", {}).get("rmse", float("inf"))))
        return pats_sorted[0]

    def _predict_ohm(self, a: Number, b: Number, x: Number) -> Number:
        return a * x + b

    def _predict_hooke(self, a: Number, b: Number, x: Number) -> Number:
        return a * x + b

    def _predict_poly2(self, a: Number, b: Number, x: Number) -> Number:
        return a * (x ** 2) + b

    def _predict_exp1(self, a: Number, b: Number, x: Number) -> Number:
        return b + math.exp(a * x)

    def _predict_power(self, A: Number, B: Number, x: Number) -> Number:
        return A * (x ** B)

    def _derive_extras(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        base = pattern.get("base")
        winner = pattern.get("winner")
        fit = pattern.get("fit", {})
        out: Dict[str, Any] = {}

        a = fit.get("a"); b = fit.get("b")

        if winner == "exp1" or base in ("rc_step", "exp1"):
            if a is not None and float(a) != 0.0:
                out["tau"] = -1.0 / float(a)
        if winner == "poly2" or base in ("poly2", "poly2_iv"):
            if a is not None:
                out["dVdI(I)"] = f"= {2*float(a)} * I"
        if winner == "ohm" or base == "ohm":
            if a is not None:
                out["Râ‰ˆ"] = float(a)
        if winner == "hooke" or base == "hooke":
            if a is not None:
                out["kâ‰ˆ"] = float(a)
        return out

    def predict(self, base: str, x: Union[Number, List[Number]]) -> Dict[str, Any]:
        pattern = self.get_pattern(base)
        winner = pattern.get("winner", base)
        fit = pattern.get("fit", {})
        a = fit.get("a"); b = fit.get("b")

        if winner == "power":
            A = a; B = b

        def one(xi: Number) -> Number:
            if winner == "ohm" or base == "ohm":
                return self._predict_ohm(float(a), float(b or 0.0), float(xi))
            if winner == "hooke" or base == "hooke":
                return self._predict_hooke(float(a), float(b or 0.0), float(xi))
            if winner == "poly2" or base in ("poly2", "poly2_iv"):
                return self._predict_poly2(float(a), float(b or 0.0), float(xi))
            if winner == "exp1" or base in ("rc_step", "exp1"):
                return self._predict_exp1(float(a), float(b or 0.0), float(xi))
            if winner == "power" or base == "power":
                return self._predict_power(float(A), float(B), float(xi)) # type: ignore
            return float(a) * float(xi) + float(b or 0.0)

        if isinstance(x, list):
            y_list = [one(v) for v in x]
            y_out = y_list
        else:
            y_out = one(x)

        derived = self._derive_extras(pattern)

        out = {
            "base": base,
            "winner": winner,
            "params": fit,
            ("y" if not isinstance(x, list) else "y_list"): y_out,
            "derived": derived,
        }
        # Attach uncertainty estimates if available and model supports predict
        try:
            if estimate_uncertainty and hasattr(self, 'model_store') and base in getattr(self, 'model_store', {}):
                model = self.model_store[base]
                # estimator expects array-like X
                res = estimate_uncertainty(model, x if isinstance(x, (list, tuple)) else [x])
                # map outputs into response; support single scalar or list
                out['ci_low'] = res.get('ci_low')
                out['ci_high'] = res.get('ci_high')
                out['sigma'] = res.get('sigma')
        except Exception:
            # never fail prediction due to uncertainty estimation
            pass
        return out

