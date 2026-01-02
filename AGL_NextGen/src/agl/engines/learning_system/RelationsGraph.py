# Learning_System/RelationsGraph.py
from dataclasses import dataclass
from typing import Dict, Callable, Any, Optional

@dataclass
class Relation:
    name: str
    forward: Callable[..., Dict[str, float]]   # يحول من نموذج أساسي إلى مشتقات/قوانين
    check_units: Optional[Callable[..., bool]] = None

class RelationsGraph:
    """
    رسم علاقات بسيط يربط القوانين المتعلمة بتحويلات طاقية/قدرات/حركيات.
    """
    def __init__(self):
        self._R: Dict[str, Relation] = {}
        self._init_relations()

    def _init_relations(self):
        # Hooke: F = k x  -> Energy: E = 1/2 k x^2
        def hooke_to_energy(k: float, x_sample: float = 1.0):
            E = 0.5 * k * (x_sample ** 2)
            return {"E": E, "k": k, "x_sample": x_sample}

        # Ohm: V = R I  -> Power forms
        def ohm_to_power(R: float, I_sample: float = 1.0, V_sample: Optional[float] = None):
            if V_sample is None:
                V_sample = R * I_sample
            P1 = V_sample * I_sample
            P2 = (I_sample ** 2) * R
            P3 = (V_sample ** 2) / R if R != 0 else float("inf")
            return {"P_VI": P1, "P_I2R": P2, "P_V2_over_R": P3, "R": R}

        # Projectile: s = v0 t - 0.5 g t^2 -> استرجاع g تقريبياً من ملاءمة poly2 (a≈-0.5g)
        def projectile_poly2_to_g(a: float):
            g = -2.0 * a
            return {"g": g, "a": a}

        # RC-step: Vc = V (1 - exp(-t/tau))  -> tau = RC
        def rc_exp_to_tau(a: float, b: float):
            # ملاءمتنا كانت على شكل: Vc ≈ b + something*exp(a*t) (إشارة a سالبة عادة)
            # هنا نُرجِع ثابت زمن تقريبي من a (إذا a ≈ -1/tau)
            tau = (-1.0 / a) if a != 0 else float("inf")
            return {"tau": tau, "a": a, "V_approx": b}

        self._R["hooke->energy"] = Relation("hooke->energy", hooke_to_energy)
        self._R["ohm->power"] = Relation("ohm->power", ohm_to_power)
        self._R["proj_poly2->g"] = Relation("proj_poly2->g", projectile_poly2_to_g)
        self._R["rc_exp->tau"] = Relation("rc_exp->tau", rc_exp_to_tau)

    def apply(self, relation_name: str, **kwargs) -> Dict[str, float]:
        if relation_name not in self._R:
            raise KeyError(f"Unknown relation: {relation_name}")
        rel = self._R[relation_name]
        out = rel.forward(**kwargs)
        if rel.check_units and (not rel.check_units(out)):
            raise ValueError(f"Units check failed for relation {relation_name}")
        return out
