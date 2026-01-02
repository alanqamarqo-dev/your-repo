from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List, Tuple
import math

@dataclass
class Hypothesis:
    name: str
    form: str
    params: Dict[str, float]


class SelfLearningModule:
    """
    مولد فرضيات بسيط + ملاءمة معاملات على بيانات صغيرة.
    الهدف: قاعدة متينة للاختبارات والتوسعة لاحقاً.
    """
    def __init__(self) -> None:
        self.learned: List[Hypothesis] = []

    def generate_hypotheses(self, law_hint: str = "") -> List[Hypothesis]:
        hyps = [
            Hypothesis(name="hooke", form="F = k * x", params={"k": 1.0}),
            Hypothesis(name="ohm",  form="V = R * I", params={"R": 1.0}),
        ]
        if law_hint and "hooke" in law_hint.lower():
            return [hyps[0], hyps[1]]
        return hyps

    def fit_params(self, hyp: Hypothesis, X: List[Dict[str, float]], y: List[float]) -> Hypothesis:
        if hyp.name == "hooke" and hyp.form == "F = k * x":
            num = 0.0; den = 0.0
            for xi, yi in zip(X, y):
                x = float(xi["x"]); F = float(yi)
                num += x * F
                den += x * x
            k = num / den if den != 0 else 0.0
            return Hypothesis(name=hyp.name, form=hyp.form, params={"k": k})

        if hyp.name == "ohm" and hyp.form == "V = R * I":
            num = 0.0; den = 0.0
            for xi, yi in zip(X, y):
                I = float(xi["I"]); V = float(yi)
                num += I * V
                den += I * I
            R = num / den if den != 0 else 0.0
            return Hypothesis(name=hyp.name, form=hyp.form, params={"R": R})

        return hyp

    def predict(self, hyp: Hypothesis, x: Dict[str, float]) -> float:
        if hyp.name == "hooke":
            return hyp.params["k"] * float(x["x"])
        if hyp.name == "ohm":
            return hyp.params["R"] * float(x["I"])
        raise ValueError("Unsupported hypothesis")

    def evaluate_mse(self, hyp: Hypothesis, X: List[Dict[str, float]], y: List[float]) -> float:
        err = 0.0
        for xi, yi in zip(X, y):
            pred = self.predict(hyp, xi)
            diff = pred - float(yi)
            err += diff * diff
        return err / max(1, len(X))
