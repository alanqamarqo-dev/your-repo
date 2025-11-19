# -*- coding: utf-8 -*-
"""
Advanced strategic planner harness.

Produces:
 - multi-year roadmap
 - scenario analysis (drivers)
 - decision matrix for strategic options
 - risk register with suggested mitigations
 - resource allocation given a budget
 - decision-tree EV estimate for major branches

Writes a JSON report to artifacts/reports/strategic_plan_<iso>.json
"""
from __future__ import annotations
import argparse
import json
import os
from datetime import datetime
import random
import statistics
from typing import List, Dict, Any

from Core_Engines.Strategic_Thinking import StrategicThinkingEngine

try:
    from Core_Engines.External_InfoProvider import ExternalInfoProvider
except Exception:
    ExternalInfoProvider = None


def build_example_options() -> List[Dict[str, Any]]:
    return [
        {"name": "Expand R&D (Innovation)", "ROI": 0.6, "risk": 0.4, "cost": 5.0, "value": 8.0},
        {"name": "Consolidate Core Products", "ROI": 0.5, "risk": 0.2, "cost": 3.0, "value": 5.0},
        {"name": "Accelerate Partnerships", "ROI": 0.4, "risk": 0.3, "cost": 2.0, "value": 4.5},
        {"name": "Open Market Expansion", "ROI": 0.7, "risk": 0.6, "cost": 7.0, "value": 10.0},
    ]


def build_example_risks() -> List[Dict[str, Any]]:
    return [
        {"id": "R1", "title": "Economic downturn", "likelihood": 0.5, "impact": 0.8},
        {"id": "R2", "title": "Key talent loss", "likelihood": 0.3, "impact": 0.7},
        {"id": "R3", "title": "Regulatory barrier", "likelihood": 0.2, "impact": 0.9},
        {"id": "R4", "title": "Core tech failure", "likelihood": 0.15, "impact": 0.95},
    ]


def main(argv: List[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Advanced Strategic Planning Harness")
    p.add_argument("--objective", default="تطوير نظام AGI متعدد المجالات", help="Strategic objective (string)")
    p.add_argument("--years", type=int, default=5, help="Long-term horizon in years")
    p.add_argument("--budget", type=float, default=10.0, help="Budget (arbitrary units)")
    p.add_argument("--stakeholders-file", default=None, help="Path to JSON file defining stakeholders and weights (optional)")
    p.add_argument("--mc-iterations", type=int, default=0, help="Run Monte Carlo risk simulation (0 = disabled)")
    p.add_argument("--use-rag", action="store_true", help="Use ExternalInfoProvider to fetch supporting facts (mock or live)")
    p.add_argument("--seed", type=int, default=123, help="RNG seed for reproducibility")
    args = p.parse_args(argv)

    eng = StrategicThinkingEngine(seed=args.seed)

    # Roadmap: translate years into horizons (short, mid, long)
    days_short = 180
    days_med = 365
    days_long = max(365, args.years * 365)
    roadmap = eng.roadmap(args.objective, horizons=(days_short, days_med, days_long))

    # Scenario analysis: drivers tuned to long-term planning
    driver_a = ("economic_conditions", ["recession", "stability", "growth"])
    driver_b = ("technology_adoption", ["slow", "steady", "rapid"])
    scenarios = eng.scenario_analysis(args.objective, driver_a, driver_b)

    # Decision matrix: options evaluated against criteria
    options = build_example_options()
    # Default criteria weights
    criteria_weights = {"ROI": 0.5, "risk": 0.2, "value": 0.3}
    # If stakeholders file provided, compute weighted aggregate criteria weights
    if args.stakeholders_file:
        try:
            with open(args.stakeholders_file, 'r', encoding='utf-8') as fh:
                st = json.load(fh)
            # expected format: {"stakeholders": [{"name":"A","weight":0.6, "criteria_weights":{...}}, ...]}
            agg: Dict[str, float] = {}
            total_w = 0.0
            for s in st.get('stakeholders', []):
                w = float(s.get('weight', 0.0))
                total_w += w
                cw = s.get('criteria_weights', {})
                for k, v in cw.items():
                    agg[k] = agg.get(k, 0.0) + float(v) * w
            if total_w > 0:
                criteria_weights = {k: (v / total_w) for k, v in agg.items()}
        except Exception:
            pass
    # The engine expects numeric fields in options; invert risk to be a positive benefit (1-risk)
    dm_opts = []
    for o in options:
        dm_opts.append({"name": o["name"], "ROI": o["ROI"], "risk": 1.0 - o["risk"], "value": o["value"]})
    decision_matrix = eng.decision_matrix(dm_opts, criteria_weights)

    # Risk register
    risks = build_example_risks()
    risk_reg = eng.risk_register(risks, thresholds=(0.4, 0.6))

    # Enhance risk register with Monte Carlo simulation results and actionable mitigations
    def _expand_mitigation_text(txt: str, r: Dict[str, Any]) -> Dict[str, Any]:
        # create an actionable mitigation structure
        owner = "Chief Risk Officer"
        est_cost = round(float(r.get('impact', 0.0)) * 10.0, 2)
        actions = [
            "تحليل السبب الجذري وتطبيق ضوابط تقنية",
            "إعداد خطة طوارئ (Fallback) وتشغيل اختبارات دوريّة",
        ]
        if "تجنب" in txt or "إعادة تصميم" in txt:
            actions.insert(0, "إعادة تصميم أو تغيير نطاق المشروع")
        trigger = "likelihood>0.6 or impact>0.6"
        return {"text": txt, "owner": owner, "estimated_cost": est_cost, "actions": actions, "trigger": trigger}

    mc_iterations = max(0, int(args.mc_iterations or 0))
    if mc_iterations > 0:
        # Monte Carlo: for each risk, sample likelihood and impact with small noise
        for r in risk_reg:
            L = float(r.get('likelihood', 0.0))
            I = float(r.get('impact', 0.0))
            samples = []
            for _ in range(mc_iterations):
                sL = min(1.0, max(0.0, random.gauss(L, 0.1)))
                sI = min(1.0, max(0.0, random.gauss(I, 0.12)))
                samples.append(sL * sI)
            mean_p = statistics.mean(samples) if samples else 0.0
            p50 = statistics.median(samples) if samples else 0.0
            # safe indexing for percentiles
            sorted_s = sorted(samples) if samples else []
            p5 = sorted_s[int(len(sorted_s)*0.05)] if sorted_s else 0.0
            p95 = sorted_s[max(0, int(len(sorted_s)*0.95)-1)] if sorted_s else 0.0
            r['mc'] = {"mean_priority": round(mean_p, 4), "p5": round(p5, 4), "p50": round(p50, 4), "p95": round(p95, 4)}
            r['mitigation_struct'] = _expand_mitigation_text(r.get('mitigation', ''), r)
    else:
        for r in risk_reg:
            r['mitigation_struct'] = _expand_mitigation_text(r.get('mitigation', ''), r)

    # Resource allocation
    projects = [
        {"name": o["name"], "cost": o["cost"], "value": o["value"], "risk": o["risk"]} for o in options
    ]
    allocation = eng.allocate_resources(projects, budget=args.budget, risk_aversion=0.35)

    # Decision tree EV: coarse branches for top strategic choices
    branches = [
        {"name": "Expand R&D", "prob": 0.4, "payoff": 12.0},
        {"name": "Consolidate", "prob": 0.3, "payoff": 6.0},
        {"name": "Market Expansion", "prob": 0.3, "payoff": 15.0},
    ]
    tree_ev = eng.decision_tree_ev(branches)

    # Evaluate sample options (compatibility method)
    evaluated_options = {o["name"]: eng.evaluate(o["name"]) for o in options}

    # Use the new advanced strategic analysis features
    # Complex scenario analysis across multiple drivers
    complex_drivers = [
        ("economic_conditions", ["recession", "stability", "growth"]),
        ("technology_adoption", ["slow", "steady", "rapid"]),
        ("regulatory", ["tight", "moderate", "lenient"]),
    ]
    complex_scenarios = eng.complex_scenario_analysis(args.objective, complex_drivers, depth=3)

    # Build simple numeric factors for SWOT analysis from heuristics
    # funding: normalize budget to a 0..1 scale assuming 20 as generous budget
    funding_score = float(min(1.0, args.budget / 20.0))
    # talent: heuristic from evaluated options (more complex could use HR metrics)
    talent_score = 0.6 + 0.1 * sum((v.get('benefit', 0.0) for v in evaluated_options.values()))
    # regulatory exposure: derive from max risk impact in risk_reg
    reg_exposure = max((float(r.get('impact', 0.0)) for r in risk_reg), default=0.0)
    tech_maturity = sum((float(o.get('ROI', 0.0)) for o in options)) / max(1, len(options))
    factors = {"funding": round(funding_score, 2), "talent": round(min(1.0, talent_score), 2), "regulatory": round(reg_exposure, 2), "tech_maturity": round(tech_maturity, 2)}
    swot = eng.analyze_swot(args.objective, factors)

    # Decision-making under uncertainty: prepare payoff model and uncertain params
    decision_options = [{"name": o["name"], "base_payoff": float(o.get("value", 0.0))} for o in options]
    payoff_model: Dict[str, Dict[str, float]] = {}
    for o in options:
        # use ROI and value as simple multipliers on market_growth and adoption
        payoff_model[o["name"]] = {"market_growth": float(o.get("ROI", 0.0)), "adoption": float(o.get("value", 0.0))}

    uncertain_params = {"market_growth": (0.2, 0.1), "adoption": (0.5, 0.2)}
    samples = 200 if mc_iterations <= 0 else min(1000, max(50, mc_iterations))
    decision_uncertainty = eng.decision_under_uncertainty(decision_options, payoff_model, uncertain_params, samples=samples, risk_aversion=0.35)

    # Synthesise a long-term plan structure spanning years
    years = args.years
    long_term_plan = []
    for y in range(1, years + 1):
        milestones = []
        if y == 1:
            milestones = ["تثبيت الأساسيات التقنية", "تجنيد فرق رئيسية", "إطلاق تجارب MVP"]
        elif y <= 2:
            milestones = ["تحسين النموذج", "تعزيز الشراكات", "إثبات القيمة في سوقين"]
        elif y <= 4:
            milestones = ["توسيع النطاق", "أتمتة العمليات", "حوكمة/التزام"]
        else:
            milestones = ["الاستدامة المالية", "توسع دولي مستهدف", "حوكمة مستقرة"]
        long_term_plan.append({"year": y, "milestones": milestones})

    report: Dict[str, Any] = {
        "meta": {
            "objective": args.objective,
            "years": years,
            "budget": args.budget,
            "generated_at": datetime.utcnow().isoformat() + "Z",
        },
        "roadmap": roadmap,
        "long_term_plan": long_term_plan,
        "scenarios": scenarios,
        "decision_matrix": decision_matrix,
        "evaluated_options": evaluated_options,
        "risk_register": risk_reg,
        "allocation": allocation,
        "mc_iterations": mc_iterations,
        "decision_tree_ev": tree_ev,
        "complex_scenarios": complex_scenarios,
        "swot": swot,
        "decision_under_uncertainty": decision_uncertainty,
    }

    # Optionally enrich report via RAG (ExternalInfoProvider)
    if args.use_rag and ExternalInfoProvider is not None:
        try:
            prov = ExternalInfoProvider()
            q = f"Provide concise factual indicators relevant to objective: {args.objective} across economic and technology signals for the next {args.years} years."
            rag = prov.fetch_facts(q, hints=["economic indicators", "technology adoption"])
            report['rag_query'] = q
            report['rag'] = rag
        except Exception as e:
            report['rag'] = {"ok": False, "error": str(e)}

    out_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "artifacts", "reports")
    os.makedirs(out_dir, exist_ok=True)
    stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    out_path = os.path.join(out_dir, f"strategic_plan_{stamp}.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)

    print(f"Wrote strategic plan report to: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
