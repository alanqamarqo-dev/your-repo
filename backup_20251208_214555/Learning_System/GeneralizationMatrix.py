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
