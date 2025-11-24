# Learning_System/Generalizer.py
import json, os
from typing import Dict, Any, Optional, Tuple
from .RelationsGraph import RelationsGraph

class Generalizer:
    """
    يأخذ نتائج النماذج (results.json) ويستنتج كميات/قوانين مشتقة
    عبر علاقات معرّفة في RelationsGraph.
    """
    def __init__(self):
        self.RG = RelationsGraph()

    def _load_results(self, path: str) -> Dict[str, Any]:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _pick_winner(self, results: Dict[str, Any]) -> Tuple[str, Dict[str, float]]:
        # يدعم شكلين: إما قائمة "results" أو "ensemble.result"
        if "ensemble" in results:
            res = results["ensemble"]["result"]
            winner = res["winner"]
            params = res.get("params", {})
            return winner, params
        else:
            # خذ أقل RMSE
            best = min(results["results"], key=lambda r: r["fit"]["rmse"])
            return best["candidate"], {"a": best["fit"]["a"], "b": best["fit"].get("b", 0.0)}

    def derive(self, results_path: str, relation_hint: Optional[str] = None, **samples) -> Dict[str, Any]:
        results = self._load_results(results_path)
        base = results.get("base", "")
        winner, params = self._pick_winner(results)

        # خرائط بسيطة من النوع الفائز إلى العلاقة المناسبة
        mapping = {
            # Hooke (k*x [+b≈0]) -> energy
            ("hooke", "hooke"): ("hooke->energy", dict(k=abs(params.get("a", 0)), **({"x_sample": samples.get("x", 1.0)}))),
            # Ohm (V=R*I) -> power
            ("ohm", "ohm"): ("ohm->power", dict(R=abs(params.get("a", 0)), I_sample=samples.get("I", 1.0))),
            # Projectile: poly2: s = a t^2 + b t + c  (عندنا في D حفظنا a,b غالباً) -> g≈-2a
            ("projectile", "poly2"): ("proj_poly2->g", dict(a=params.get("a", 0))),
            # RC-step: exp1: Vc ≈ b + A*exp(a t)  -> tau ≈ -1/a
            ("rc_step", "exp1"): ("rc_exp->tau", dict(a=params.get("a", -1.0), b=params.get("b", 0.0))),
        }

        key = (base, winner)
        if relation_hint:
            rel_name = relation_hint
            args = samples
        else:
            if key not in mapping:
                raise ValueError(f"No default generalization mapping for base={base}, winner={winner}")
            rel_name, args = mapping[key]

        derived = self.RG.apply(rel_name, **args)
        return {
            "base": base,
            "winner": winner,
            "relation": rel_name,
            "inputs": {"params": params, **args},
            "derived": derived
        }
