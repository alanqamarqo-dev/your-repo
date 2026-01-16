from typing import List, Dict, Any, Tuple
import math
import random
from typing import List, Dict, Any, Tuple
import math
import random

try:
    from Core_Engines.engine_base import EngineBase  # type: ignore
except Exception:
    class EngineBase:
        name: str = "EngineBase"
        version: str = "0.0"
        capabilities: List[str] = []
        def info(self) -> Dict[str, Any]:
            return {"name": self.name, "version": self.version, "capabilities": self.capabilities}


class StrategicThinkingEngine(EngineBase): # type: ignore
    """
    محرك التفكير الاستراتيجي: MCDA, risk register, scenarios, allocation, decision tree EV, roadmap
    """
    name = "StrategicThinkingEngine"
    version = "1.0.0"
    capabilities = [
        "multi_criteria_decision",
        "risk_matrix",
        "scenario_planning",
        "resource_allocation",
        "decision_tree_ev",
        "roadmapping",
        "quantum_strategic_analysis",
    ]

    def __init__(self, seed: int = 123) -> None:
        self._rng = random.Random(seed)

    def healthcheck(self) -> Dict[str, Any]:
        """Instance-level healthcheck for monitoring probes.

        Keep side-effect free and fast.
        """
        try:
            return {
                "ok": True,
                "engine": self.name,
                "version": getattr(self, 'version', '1.0.0'),
                "capabilities": getattr(self, 'capabilities', []),
                "uptime_s": 0,
            }
        except Exception:
            return {"ok": False, "engine": getattr(self, 'name', 'StrategicThinkingEngine')}

    def decision_matrix(
        self,
        options: List[Dict[str, Any]],
        criteria_weights: Dict[str, float],
        normalize: bool = True,
    ) -> List[Dict[str, Any]]:
        if not options:
            return []

        crits = list(criteria_weights.keys())
        data = []
        mins: Dict[str, float] = {}
        maxs: Dict[str, float] = {}
        if normalize:
            for c in crits:
                vals = [float(opt.get(c, 0.0)) for opt in options]
                mins[c] = min(vals) if vals else 0.0
                maxs[c] = max(vals) if vals else 1.0

        def norm(c: str, v: float) -> float:
            if not normalize:
                return float(v)
            lo, hi = mins[c], maxs[c]
            if math.isclose(hi, lo):
                return 0.0
            return (float(v) - lo) / (hi - lo)

        total_w = sum(criteria_weights.values()) or 1.0
        for opt in options:
            score = 0.0
            breakdown: Dict[str, float] = {}
            for c, w in criteria_weights.items():
                v = norm(c, float(opt.get(c, 0.0)))
                part = v * (w / total_w)
                breakdown[c] = round(part, 4)
                score += part
            data.append({"name": opt.get("name", "option"), "score": round(score, 4), "breakdown": breakdown})

        data.sort(key=lambda x: x["score"], reverse=True)
        return data

    def risk_register(
        self,
        risks: List[Dict[str, Any]],
        thresholds: Tuple[float, float] = (0.5, 0.5),
    ) -> List[Dict[str, Any]]:
        hiL, hiI = thresholds
        out: List[Dict[str, Any]] = []
        for r in risks:
            L = float(r.get("likelihood", 0.0))
            I = float(r.get("impact", 0.0))
            p = round(L * I, 4)
            if L >= hiL and I >= hiI:
                band = "High"
            elif p >= 0.25:
                band = "Medium"
            else:
                band = "Low"
            out.append({**r, "priority": p, "band": band, "mitigation": self._suggest_mitigation(L, I)})
        out.sort(key=lambda x: x["priority"], reverse=True)
        return out

    def _suggest_mitigation(self, L: float, I: float) -> str:
        if L >= 0.7 and I >= 0.7:
            return "تجنب/إعادة تصميم الخطة، أو نقل الخطر بالتأمين/الشراكات."
        if I >= 0.7:
            return "تخفيف الأثر عبر ضوابط/عوازل وتقليل التعرض."
        if L >= 0.7:
            return "تقليل الاحتمال عبر ضوابط وقائية/تحكم في الأسباب."
        return "راقب الخطر وخطط استجابة مبسطة."

    def scenario_analysis(
        self,
        title: str,
        driver_a: Tuple[str, List[str]],
        driver_b: Tuple[str, List[str]],
    ) -> Dict[str, Any]:
        (a_name, a_levels) = driver_a
        (b_name, b_levels) = driver_b
        a = (a_levels + ["منخفض", "مرتفع"])[:2]
        b = (b_levels + ["منخفض", "مرتفع"])[:2]
        scenarios = []
        for ai in a:
            for bi in b:
                tag = f"{a_name}:{ai} × {b_name}:{bi}"
                key = f"{ai[:2]}-{bi[:2]}"
                thesis = f"فرضية: إذا كان {a_name}={ai} و{b_name}={bi} فسنحتاج استراتيجية ملائمة للمخاطر والموارد."
                kpis = ["ROI", "CAC", "Time-to-Value"] if "مرتفع" in (ai + bi) else ["Runway", "Reliability"]
                scenarios.append({"key": key, "label": tag, "thesis": thesis, "kpi": kpis})
        return {"title": title, "drivers": [a_name, b_name], "grid": scenarios}

    def allocate_resources(
        self,
        projects: List[Dict[str, Any]],
        budget: float,
        risk_aversion: float = 0.3,
    ) -> Dict[str, Any]:
        if budget <= 0 or not projects:
            return {"selected": [], "spent": 0.0, "expected_value": 0.0}

        items = []
        for p in projects:
            cost = float(p.get("cost", 0.0)) or 1e-9
            value = float(p.get("value", 0.0))
            risk = min(1.0, max(0.0, float(p.get("risk", 0.0))))
            density = value * (1.0 - risk_aversion * risk) / cost
            items.append({**p, "density": density})

        items.sort(key=lambda x: (x["density"], x["value"]), reverse=True)

        selected: List[Dict[str, Any]] = []
        spent = 0.0
        exp_val = 0.0
        for it in items:
            if spent + it["cost"] <= budget + 1e-9:
                selected.append({"name": it["name"], "cost": it["cost"], "value": it["value"], "risk": it["risk"]})
                spent += float(it["cost"])
                exp_val += float(it["value"]) * (1.0 - risk_aversion * float(it["risk"]))

        return {"selected": selected, "spent": round(spent, 3), "expected_value": round(exp_val, 3)}

    def decision_tree_ev(self, branches: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not branches:
            return {"ev": 0.0, "best": None}
        ev = 0.0
        best = None
        best_val = -1e9
        for b in branches:
            p = float(b.get("prob", 0.0))
            payoff = float(b.get("payoff", 0.0))
            ev += p * payoff
            if payoff > best_val:
                best_val = payoff
                best = b.get("name", "branch")
        return {"ev": round(ev, 4), "best": best}

    def roadmap(self, objective: str, horizons: Tuple[int, int, int] = (90, 180, 365)) -> List[Dict[str, Any]]:
        s, m, l = horizons
        return [
            {"horizon_days": s, "objective": objective, "milestones": ["تحديد مؤشرات النجاح", "MVP", "تجارب جدوى"]},
            {"horizon_days": m, "objective": objective, "milestones": ["تحسين العملية", "شراكات", "توسعة محسوبة"]},
            {"horizon_days": l, "objective": objective, "milestones": ["أتمتة", "حوكمة/امتثال", "توسع دولي"]},
        ]

    # compatibility: older tests expect .plan(objective, n)
    def plan(self, objective: str, n: int = 3) -> List[Dict[str, Any]]:
        # produce a roadmap and return first n horizon entries
        return self.roadmap(objective)[: max(1, int(n))]

    # compatibility: evaluate an option into benefit/risk/tradeoff
    def evaluate(self, option: str) -> Dict[str, float]:
        # naive heuristics: length-based benefit, random risk based on seed
        benefit = min(1.0, len(option) / 10.0)
        risk = round(min(1.0, 0.3 + (len(option) % 5) * 0.1), 3)
        tradeoff = round(max(0.0, benefit - risk), 3)
        return {"benefit": round(benefit, 3), "risk": risk, "tradeoff": tradeoff}

    # compatibility alias
    def scenarios(self, objective: str) -> List[Dict[str, Any]]:
        # provide drivers default
        grid = self.scenario_analysis(objective, ("market", ["low","high"]), ("tech", ["slow","fast"]))["grid"]
        return grid[:3]

    def complex_scenario_analysis(
        self,
        title: str,
        drivers: List[Tuple[str, List[str]]],
        depth: int = 3,
    ) -> Dict[str, Any]:
        """
        Perform a richer scenario analysis over multiple drivers.

        Args:
            title: scenario title
            drivers: list of (driver_name, [levels...])
            depth: how detailed (controls heuristic confidence)

        Returns:
            dict with grid of scenarios, for each scenario a SWOT-like analysis,
            recommended strategic posture and a confidence score.
        """
        # Build combinations (cartesian) but cap to reasonable size
        lists = [levels for (_name, levels) in drivers]
        names = [name for (name, _levels) in drivers]
        combos = [[]]
        for levs in lists:
            new = []
            for c in combos:
                for lv in levs:
                    new.append(c + [lv])
            combos = new
        # limit growth
        max_cells = max(1, min(len(combos), 20))
        combos = combos[:max_cells]

        grid = []
        for c in combos:
            tag_parts = [f"{n}:{v}" for n, v in zip(names, c)]
            label = " × ".join(tag_parts)
            # produce heuristic SWOT
            strengths = []
            weaknesses = []
            opportunities = []
            threats = []
            confidence = 0.5 + 0.05 * depth
            for v in c:
                if any(k in v.lower() for k in ("growth", "rapid", "high", "strong", "opportunity")):
                    strengths.append(f"ارتفاع مؤشر {v}")
                    opportunities.append(f"استثمار استغلال {v}")
                    confidence += 0.02
                if any(k in v.lower() for k in ("recession", "slow", "low", "decline")):
                    weaknesses.append(f"انخفاض {v}")
                    threats.append(f"ضغط على السيولة بسبب {v}")
                    confidence -= 0.03
            # recommended posture heuristics
            posture = "balanced"
            if any("recession" in vv.lower() or "slow" in vv.lower() for vv in c):
                posture = "defensive"
            if any("growth" in vv.lower() or "rapid" in vv.lower() for vv in c):
                posture = "growth"

            grid.append(
                {
                    "label": label,
                    "drivers": dict(zip(names, c)),
                    "swot": {"strengths": strengths, "weaknesses": weaknesses, "opportunities": opportunities, "threats": threats},
                    "recommended_posture": posture,
                    "confidence": round(min(0.95, max(0.05, confidence)), 2),
                }
            )

        return {"title": title, "drivers": names, "grid": grid}

    def analyze_swot(self, context: str, factors: Dict[str, float]) -> Dict[str, Any]:
        """
        Generate a simple SWOT (Strengths, Weaknesses, Opportunities, Threats)
        from numeric factor inputs.

        factors: dict of factor_name -> score (0..1) where higher is more positive
        """
        strengths = []
        weaknesses = []
        opportunities = []
        threats = []
        for k, v in factors.items():
            try:
                val = float(v)
            except Exception:
                val = 0.0
            if val >= 0.7:
                strengths.append(f"{k} (قوي: {val})")
            elif val >= 0.4:
                opportunities.append(f"{k} (فرصة: {val})")
            elif val >= 0.2:
                weaknesses.append(f"{k} (ضعيف: {val})")
            else:
                threats.append(f"{k} (مهدد: {val})")

        return {"context": context, "strengths": strengths, "weaknesses": weaknesses, "opportunities": opportunities, "threats": threats}

    def decision_under_uncertainty(
        self,
        options: List[Dict[str, Any]],
        payoff_model: Dict[str, Dict[str, float]],
        uncertain_params: Dict[str, Tuple[float, float]],
        samples: int = 1000,
        risk_aversion: float = 0.3,
    ) -> Dict[str, Any]:
        """
        Evaluate options under parametric uncertainty using Monte Carlo sampling.

        - options: list of options with 'name' key
        - payoff_model: mapping option_name -> mapping param_name -> base payoff multiplier
        - uncertain_params: mapping param_name -> (mean, stdev)

        Returns expected value estimates and robust choice recommendations.
        """
        if not options:
            return {"ev": {}, "best_ev": None, "robust": None}

        samples = max(10, int(samples))
        evs: Dict[str, List[float]] = {o.get("name", f"opt{i}"): [] for i, o in enumerate(options)}

        for _ in range(samples):
            # sample params
            sample_vals: Dict[str, float] = {}
            for pname, (mu, sigma) in uncertain_params.items():
                # use gaussian sampling but trunc to [0, inf)
                val = max(0.0, self._rng.gauss(float(mu), float(sigma)))
                sample_vals[pname] = val

            # evaluate each option
            for o in options:
                name = o.get("name", "option")
                model = payoff_model.get(name, {})
                # base payoff (allow constant)
                base = float(o.get("base_payoff", 0.0))
                payoff = base
                # apply param multipliers
                for p, mult in model.items():
                    mul = float(mult)
                    val = float(sample_vals.get(p, 1.0))
                    payoff += mul * val
                # apply risk aversion penalty (variance-based)
                evs[name].append(payoff)

        summary: Dict[str, Any] = {}
        best_ev = None
        best_ev_val = -1e18
        # compute EV and risk metrics
        for name, vals in evs.items():
            meanv = sum(vals) / len(vals)
            var = max(0.0, sum((x - meanv) ** 2 for x in vals) / len(vals))
            sd = var ** 0.5
            risk_adj = meanv - risk_aversion * sd
            summary[name] = {"mean": round(meanv, 4), "sd": round(sd, 4), "risk_adj": round(risk_adj, 4)}
            if meanv > best_ev_val:
                best_ev_val = meanv
                best_ev = name

        # robust choice: maximin (choose option with highest worst-case quantile)
        worst_q = -1e18
        robust_choice = None
        for name, vals in evs.items():
            q05 = sorted(vals)[max(0, int(len(vals) * 0.05) - 1)] if vals else 0.0
            if q05 > worst_q:
                worst_q = q05
                robust_choice = name

        return {"ev": summary, "best_ev": best_ev, "robust": robust_choice}

    def quantum_strategic_analysis(
        self,
        options: List[Dict[str, Any]],
        risks: List[Dict[str, Any]],
        coherence_factor: float = 0.8
    ) -> List[Dict[str, Any]]:
        """
        Applies Quantum-Synaptic Resonance to strategic options.
        Uses WKB Tunneling to evaluate if high-risk options are worth taking (tunneling through the barrier).
        Uses Resonance Amplification to boost options that align with multiple strategic drivers.
        """
        try:
            from Core_Engines.Resonance_Optimizer import ResonanceOptimizer
            optimizer = ResonanceOptimizer()
        except ImportError:
            # Fallback if ResonanceOptimizer is not available
            return self.decision_matrix(options, {"default": 1.0})

        results = []
        
        # Calculate global risk barrier height (average risk impact)
        avg_risk_impact = sum(float(r.get("impact", 0.5)) for r in risks) / len(risks) if risks else 0.5
        
        for opt in options:
            # 1. Calculate Base Energy (Value of the option)
            # Assume option has 'value' or 'score', default to 0.5
            base_energy = float(opt.get("value", opt.get("score", 0.5)))
            
            # 2. Calculate Barrier Width (Specific risk of this option)
            # Assume option has 'risk_factor', default to avg_risk_impact
            barrier_width = float(opt.get("risk_factor", avg_risk_impact))
            
            # 3. Calculate Tunneling Probability (Can we overcome the risk?)
            # Barrier height is fixed at 1.0 (max risk), energy is our capability
            # We set the barrier width (L) on the optimizer instance
            optimizer.L = barrier_width
            
            # Energy Diff = Capability - Barrier Height
            # If Capability > Barrier, we pass freely. If < Barrier, we tunnel.
            energy_diff = base_energy - 1.0
            
            tunneling_prob = optimizer._wkb_tunneling_prob(
                energy_diff=energy_diff,
                barrier_height=1.0
            )
            
            # 4. Calculate Resonance (Alignment with strategic drivers)
            # Natural Frequency w0 = 1.0 (Ideal Strategic Alignment)
            # Signal Frequency w = 1.0 if aligned, else 0.5
            w0 = 1.0
            w = 1.0 if opt.get("aligned", False) else 0.5
            
            # Gamma (Damping) is inverse of coherence factor
            # High coherence (0.9) -> Low Gamma (0.1) -> High Resonance
            gamma = max(0.01, 1.0 - coherence_factor)
            
            resonance_amp = optimizer._resonance_amplification(
                signal_freq=w,
                natural_freq=w0,
                gamma=gamma
            )
            
            # Final Quantum Score
            # We combine Tunneling (overcoming risk) and Resonance (amplifying value)
            # Formula: Score = Base * Resonance * (1 + Tunneling)
            quantum_score = base_energy * resonance_amp * (1 + tunneling_prob)
            
            results.append({
                "name": opt.get("name", "Unknown"),
                "base_value": base_energy,
                "risk_barrier": barrier_width,
                "tunneling_prob": tunneling_prob,
                "resonance_amp": resonance_amp,
                "quantum_score": quantum_score,
                "recommendation": "Pursue (Quantum Tunneling)" if tunneling_prob > 0.5 and quantum_score > 0.8 else "Standard"
            })
            
        results.sort(key=lambda x: x["quantum_score"], reverse=True)
        return results

    # compatibility: provide a small process_task expected by bootstrap/tests
    def process_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # simple router: if 'objective' provided, return a roadmap; else healthcheck
        try:
            if not payload:
                return {"ok": True, "engine": self.name, "msg": "no-op"}
            obj = payload.get("objective") or payload.get("task")
            if obj:
                return {"ok": True, "engine": self.name, "result": self.plan(str(obj), n=3)}
            # fallback: return health/status
            return {"ok": True, "engine": self.name, "status": self.healthcheck()}
        except Exception as e:
            return {"ok": False, "engine": self.name, "error": str(e)}


def healthcheck() -> Dict[str, Any]:
    """Module-level healthcheck for StrategicThinking engine used by probes.

    Returns a small JSON-serializable status dict.
    """
    try:
        return {
            "ok": True,
            "engine": "Strategic_Thinking",
            "version": StrategicThinkingEngine.version if hasattr(StrategicThinkingEngine, 'version') else "1.0.0",
            "uptime_s": 0,
            "capabilities": StrategicThinkingEngine.capabilities if hasattr(StrategicThinkingEngine, 'capabilities') else []
        }
    except Exception:
        return {"ok": False, "engine": "Strategic_Thinking"}


# Backwards-compatible alias expected by ENGINE_SPECS
StrategicThinking = StrategicThinkingEngine  # type: ignore

