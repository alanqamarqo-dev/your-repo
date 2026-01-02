# -*- coding: utf-8 -*-
"""
Learning_System.Reasoner
مستدلّ نشط يقرأ الأنماط المتعلّمة ويرد على أسئلة تفسيرية.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional, List, Tuple
import json, re, math
from pathlib import Path
from datetime import datetime, timezone

KB_DEFAULT = Path("Knowledge_Base/Learned_Patterns.json")

@dataclass
class Answer:
    ok: bool
    question: str
    result: Dict[str, Any]
    reasoning: str
    ts_iso: str

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _load_kb(kb_path: Path = KB_DEFAULT) -> Dict[str, Any]:
    p = Path(kb_path)
    if not p.exists():
        raise FileNotFoundError(f"KB not found: {p}")
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)

def _pick_latest_fit(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    return entries[-1]

def _find_by_base(kb: Dict[str, Any], base: str) -> Optional[Dict[str, Any]]:
    patterns = kb.get("patterns", [])
    group = [e for e in patterns if e.get("base", "").lower() == base.lower()]
    if not group:
        return None
    return _pick_latest_fit(group)

def _arabic_or_english(text: str, *alts: str) -> bool:
    """Match any alternative in the text.

    For ASCII-only tokens (like single letters `g`, `r`, `k` or words like `ohm`),
    use word-boundary regex to avoid substring false-positives (e.g. 'g' in
    'spring'). For non-ASCII tokens (Arabic words) fall back to simple
    substring check because word boundaries are not reliable across scripts.
    """
    t = text.lower()
    for a in alts:
        if not a:
            continue
        a_l = a.lower()
        # If token is purely ASCII letters/digits/underscore/hyphen, use \b
        if re.fullmatch(r"[A-Za-z0-9_-]+", a_l):
            if re.search(rf"\b{re.escape(a_l)}\b", t):
                return True
        else:
            if a_l in t:
                return True
    return False

def _num_from_question(q: str, keys: List[str]) -> Optional[float]:
    for k in keys:
        m = re.search(rf"{re.escape(k)}\s*=\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)", q)
        if m:
            try:
                return float(m.group(1))
            except ValueError:
                pass
    return None

class Reasoner:
    def __init__(self, kb_path: Path = KB_DEFAULT):
        self.kb_path = Path(kb_path)
        self.kb = _load_kb(self.kb_path)

    def refresh(self):
        self.kb = _load_kb(self.kb_path)

    def query(self, question: str) -> Answer:
        q = question.strip()
        now = _utcnow_iso()

        # 1) RC step: τ = -1/a
        if _arabic_or_english(q, "rc", "rc_step", "الثابت الزمني", "tau", "زمن ثابت"):
            entry = _find_by_base(self.kb, "rc_step") or _find_by_base(self.kb, "exp1")
            if not entry:
                return Answer(False, q, {}, "لا يوجد نمط RC في القاعدة.", now)
            a = entry["fit"]["a"]
            tau = float("inf") if a == 0 else -1.0 / a
            return Answer(True, q, {
                "base": entry["base"],
                "winner": entry.get("winner"),
                "params": entry["fit"],
                "tau": tau
            }, "استخدمنا العلاقة τ = -1/a من نموذج الشحنة الأسّي.", now)

        # 2) Projectile: g ≈ 2a
        if _arabic_or_english(q, "projectile", "مقذوف", "g", "تسارع الجاذبية"):
            entry = _find_by_base(self.kb, "projectile")
            if not entry:
                return Answer(False, q, {}, "لا يوجد نمط Projectile في القاعدة.", now)
            a = entry["fit"]["a"]
            g = 2.0 * a
            return Answer(True, q, {
                "base": entry["base"],
                "winner": entry.get("winner"),
                "params": entry["fit"],
                "g_approx": g
            }, "استخدمنا g ≈ 2·a من النموذج التربيعي للحركة.", now)

        # 3) Ohm: R ≈ a  (V ≈ a·I + b)
        if _arabic_or_english(q, "ohm", "أوم", "المقاومة", "resistance", "r=", "r"):
            entry = _find_by_base(self.kb, "ohm")
            if not entry:
                return Answer(False, q, {}, "لا يوجد نمط أوم في القاعدة.", now)
            R = entry["fit"]["a"]
            return Answer(True, q, {
                "base": entry["base"],
                "winner": entry.get("winner"),
                "params": entry["fit"],
                "R": R
            }, "من V(I) ≈ a·I + b ⇒ R ≈ a.", now)

        # 4) Hooke: k ≈ a (F ≈ a·x + b)
        if _arabic_or_english(q, "hooke", "هوك", "ثابت النابض", "spring", "k="):
            entry = _find_by_base(self.kb, "hooke")
            if not entry:
                return Answer(False, q, {}, "لا يوجد نمط هوك في القاعدة.", now)
            k = entry["fit"]["a"]
            return Answer(True, q, {
                "base": entry["base"],
                "winner": entry.get("winner"),
                "params": entry["fit"],
                "k": k
            }, "من F(x) ≈ a·x + b ⇒ k ≈ a.", now)

        # 5) poly2: dV/dI = 2·a·I (إذا توفّر I=.. في السؤال)
        if _arabic_or_english(q, "poly2", "تربيعي", "dV/dI", "مقاومة تفاضلية", "differential"):
            entry = _find_by_base(self.kb, "poly2") or _find_by_base(self.kb, "poly2_iv")
            if not entry:
                return Answer(False, q, {}, "لا يوجد نمط تربيعي في القاعدة.", now)
            I = _num_from_question(q, ["I", "i"])
            a = entry["fit"]["a"]
            if I is None:
                return Answer(True, q, {
                    "base": entry["base"],
                    "winner": entry.get("winner"),
                    "params": entry["fit"],
                    "formula": "dV/dI(I) = 2·a·I"
                }, "المطلوب قيمة I لحساب dV/dI عددياً. عرضنا الصيغة العامة.", now)
            dVdI = 2.0 * a * I
            return Answer(True, q, {
                "base": entry["base"],
                "winner": entry.get("winner"),
                "params": entry["fit"],
                "I": I,
                "dVdI": dVdI
            }, "من V ≈ a·I² + b ⇒ dV/dI = 2·a·I.", now)

        # 6) exp1 عام: إعطاء τ إن كان a<0 أو عرض الصيغة
        if _arabic_or_english(q, "exp1", "أسي", "exponential"):
            entry = _find_by_base(self.kb, "exp1")
            if not entry:
                return Answer(False, q, {}, "لا يوجد exp1 في القاعدة.", now)
            a = entry["fit"]["a"]
            res: Dict[str, Any] = {
                "base": entry["base"],
                "winner": entry.get("winner"),
                "params": entry["fit"],
                "schema": "y ≈ b + exp(a·x)"
            }
            if a < 0:
                res["tau"] = -1.0 / a
                reason = "a < 0 ⇒ τ = -1/a."
            else:
                reason = "نموذج أسي عام؛ τ معرف فقط عندما a<0."
            return Answer(True, q, res, reason, now)

        # 7) fallback: عرض أقرب نمط معروف مذكور في السؤال
        for base in ["ohm", "hooke", "projectile", "rc_step", "poly2", "poly2_iv", "exp1", "power"]:
            if base in q.lower():
                entry = _find_by_base(self.kb, base)
                if entry:
                    return Answer(True, q, {
                        "base": entry["base"],
                        "winner": entry.get("winner"),
                        "params": entry["fit"],
                        "schema": entry.get("schema")
                    }, "سردنا تفاصيل النمط الأقرب المذكور في السؤال.", now)

        return Answer(False, q, {}, "لم أتعرف على المقصود. اذكر المجال (ohm/hooke/projectile/rc_step/poly2/exp1) أو كمية مثل τ، g، R، k.", now)
