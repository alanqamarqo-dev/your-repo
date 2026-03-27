# -*- coding: utf-8 -*-
"""
GeneralizationMatrix – مصفوفة التعميم الذكي
- تقرأ الأنماط الفائزة من Knowledge_Base/Learned_Patterns.json
- تستنتج علاقات فيزيائية مشتقة/مركّبة (Ohm -> Power, RC exp -> tau, Projectile -> g, Poly2 -> dV/dI ...)
- تحفظ المخرجات في artifacts/generalization/*.json
"""
from __future__ import annotations
import json, os, math
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

UTC = timezone.utc

@dataclass
class Pattern:
    base: str
    winner: str
    fit: Dict[str, Any]
    schema: Optional[str] = None
    units: Optional[Dict[str, str]] = None
    derived: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None

def _now_iso() -> str:
    return datetime.now(UTC).isoformat()

def _load_patterns(kb_path: str) -> List[Pattern]:
    with open(kb_path, "r", encoding="utf-8") as f:
        kb = json.load(f)
    out: List[Pattern] = []
    for p in kb.get("patterns", []):
        out.append(Pattern(
            base=p.get("base",""),
            winner=p.get("winner",""),
            fit=p.get("fit",{}),
            schema=p.get("schema"),
            units=p.get("units"),
            derived=p.get("derived"),
            notes=p.get("notes"),
        ))
    return out

def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

# ---------- قواعد التعميم ----------
def infer_ohm_to_power(p: Pattern) -> Optional[Dict[str, Any]]:
    # V(I) ≈ a*I + b  => P(I)=V*I = a*I^2 + b*I
    if p.base.lower() == "ohm" and p.winner.lower() == "ohm":
        a = float(p.fit.get("a", 0.0))
        b = float(p.fit.get("b", 0.0))
        return {
            "relation": "ohm->power",
            "inputs": {"R≈": a, "V0≈": b},
            "derived": {"P(I)": f"{a:.6g}*I^2 + {b:.6g}*I"},
            "explain": "From V=a·I+b, P=V·I=a·I² + b·I",
        }
    return None

def infer_rc_tau(p: Pattern) -> Optional[Dict[str, Any]]:
    # Vc(t) ≈ b + exp(a·t) -> tau = -1/a  (عندما a<0)
    if p.base.lower() in ("rc_step","exp1") and p.winner.lower() == "exp1":
        a = float(p.fit.get("a", 0.0))
        b = float(p.fit.get("b", 0.0))
        if a != 0.0:
            tau = -1.0/a
            return {
                "relation": "rc_exp->tau",
                "inputs": {"a": a, "b": b},
                "derived": {"tau": tau, "V_approx": b, "a": a},
                "explain": "For y=b+exp(a·t), tau = -1/a if a<0.",
            }
    return None

def infer_projectile_g(p: Pattern) -> Optional[Dict[str, Any]]:
    # s(t) ≈ a·t^2 + b·t (+ c≈0) -> g ≈ 2·a
    if p.base.lower() == "projectile" and p.winner.lower() == "poly2":
        a = float(p.fit.get("a", 0.0))
        g = 2.0*a
        return {
            "relation": "projectile->g",
            "inputs": {"a": a},
            "derived": {"g": g},
            "explain": "For s=a·t²+bt, g≈2·a.",
        }
    return None


def infer_poly2_gradient(p: Pattern) -> Optional[Dict[str, Any]]:
    # poly2 V(I)=a·I^2 + b  -> dV/dI = 2aI (مشتق تفاضلي)
    if p.winner.lower() == "poly2":
        a = float(p.fit.get("a", 0.0))
        return {
            "relation": "poly2->differential_slope",
            "inputs": {"a": a},
            "derived": {"dV/dI(I)": f"{2*a:.6g}*I"},
            "explain": "For y=a·x²+b, dy/dx=2a·x.",
        }
    return None

# ---------- Quantum Generalization ----------

try:
    # Attempt local NextGen import first
    from agl.engines.resonance_optimizer import VectorizedResonanceOptimizer as ResonanceOptimizer
except ImportError:
    try:
        # Attempt import from Core_Engines for backward compatibility
        from Core_Engines.Resonance_Optimizer import ResonanceOptimizer
    except ImportError:
        ResonanceOptimizer = None

def quantum_discover_relations(patterns: List[Pattern]) -> List[Dict[str, Any]]:
    """
    Uses Quantum-Synaptic Resonance to find hidden links between disparate patterns.
    It treats 'Numerical Similarity' as Energy and 'Contextual Difference' as a Barrier.
    If Energy resonates enough to tunnel through the Barrier, a link is proposed.
    """
    if not ResonanceOptimizer:
        return []
    
    optimizer = ResonanceOptimizer()
    links = []
    
    for i in range(len(patterns)):
        for j in range(i + 1, len(patterns)):
            p1 = patterns[i]
            p2 = patterns[j]
            
            # 1. Calculate Resonance (Energy) based on numerical parameter matching
            best_match_score = 0.0
            matched_keys = ("", "")
            
            # Compare all numeric parameters
            for k1, v1 in p1.fit.items():
                if not isinstance(v1, (int, float)): continue
                for k2, v2 in p2.fit.items():
                    if not isinstance(v2, (int, float)): continue
                    
                    # Calculate similarity
                    diff = abs(v1 - v2)
                    avg = (abs(v1) + abs(v2)) / 2.0
                    if avg == 0: 
                        if diff == 0: score = 1.0
                        else: score = 0.0
                    else:
                        rel_diff = diff / avg
                        # Sharp resonance peak: exp(-5 * relative_error)
                        score = math.exp(-5.0 * rel_diff)
                    
                    if score > best_match_score:
                        best_match_score = score
                        matched_keys = (k1, k2)
            
            # 2. Calculate Barrier (Contextual Distance)
            barrier = 0.0
            if p1.base != p2.base: barrier += 0.4      # Different dataset/origin
            if p1.winner != p2.winner: barrier += 0.3  # Different mathematical model
            if p1.schema != p2.schema: barrier += 0.2  # Different schema
            
            # 3. Quantum Tunneling Calculation
            # Energy Diff = Resonance - Barrier
            # If Resonance > Barrier, we have classical connection (Energy Diff > 0)
            # If Resonance < Barrier, we need Tunneling (Energy Diff < 0)
            energy_diff = best_match_score - barrier
            
            # Use the optimizer's WKB tunneling probability
            prob = optimizer._wkb_tunneling_prob(energy_diff, barrier)
            
            # Threshold for "Quantum Insight"
            if prob > 0.15: 
                links.append({
                    "relation": "quantum_isomorphism",
                    "patterns": [p1.base, p2.base],
                    "matched_params": {
                        "p1_key": matched_keys[0], 
                        "p1_val": p1.fit.get(matched_keys[0]),
                        "p2_key": matched_keys[1],
                        "p2_val": p2.fit.get(matched_keys[1])
                    },
                    "resonance_score": float(best_match_score),
                    "barrier_height": float(barrier),
                    "tunneling_prob": float(prob),
                    "explain": f"Quantum Link: '{p1.base}' and '{p2.base}' resonate (Score {best_match_score:.2f}) tunneling through barrier {barrier:.2f} (Prob {prob:.2f})."
                })
                
    return links


RULES = [
    infer_ohm_to_power,
    infer_rc_tau,
    infer_projectile_g,
    infer_poly2_gradient,
]

def run_generalization(kb_path: str, out_dir: str) -> Dict[str, Any]:
    patterns = _load_patterns(kb_path)
    _ensure_dir(out_dir)
    derived_all: List[Dict[str, Any]] = []
    for p in patterns:
        for rule in RULES:
            try:
                r = rule(p)
                if r:
                    rec = {
                        "base": p.base,
                        "winner": p.winner,
                        "ts": _now_iso(),
                        **r
                    }
                    derived_all.append(rec)
            except Exception as e:
                derived_all.append({
                    "base": p.base, "winner": p.winner,
                    "relation": f"{rule.__name__}::error",
                    "error": str(e), "ts": _now_iso()
                })

    # حفظ ملف شامل + ملفات مفصّلة لكل علاقة
    bundle = {
        "version": "H.1",
        "generated_at": _now_iso(),
        "count": len(derived_all),
        "items": derived_all,
    }
    with open(os.path.join(out_dir, "generalization_bundle.json"), "w", encoding="utf-8") as f:
        json.dump(bundle, f, ensure_ascii=False, indent=2)

    # ملفات تفصيلية مصنّفة باسم العلاقة
    by_rel: Dict[str, List[Dict[str, Any]]] = {}
    for it in derived_all:
        rel = it.get("relation", "misc")
        by_rel.setdefault(rel, []).append(it)
    for rel, items in by_rel.items():
        safe = rel.replace("->","_").replace("/","_")
        path = os.path.join(out_dir, f"{safe}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"relation": rel, "items": items}, f, ensure_ascii=False, indent=2)

    return bundle
