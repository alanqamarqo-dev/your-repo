"""Tri-Verify layer: Units/Math Checker, Consistency Checker, Safety Gate + Rollback.

This module provides small, conservative heuristics to validate the LLM's
draft before it is returned to the user. It is intentionally lightweight and
meant to be a safety/quality gate: more sophisticated checks (symbolic math
parsing, unit algebra, or external policy engines) can be plugged later.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Iterable, Optional


NUM_RE = re.compile(r"[-+]?(?:\d+\.?\d*|\d*\.?\d+)(?:[eE][-+]?\d+)?")
UNIT_TOKENS = ["m", "cm", "mm", "km", "kg", "g", "s", "ms", "A", "K", "mol", "%"]


def _extract_numbers(text: str) -> List[str]:
    return NUM_RE.findall(text or "")


def units_math_checker(tool_outputs: Iterable[Dict[str, Any]], draft_text: str) -> Dict[str, Any]:
    """Check numerical and simple unit consistency between tool outputs and draft.

    Returns: {passed: bool, notes: [...], corrections: {...}}
    """
    notes: List[str] = []
    corrections: Dict[str, Any] = {}

    draft_nums = _extract_numbers(draft_text)

    # collect numbers from tool outputs (strings)
    tool_nums: List[str] = []
    tool_texts: List[str] = []
    for t in tool_outputs:
        out = t.get("out") or {}
        # prefer explicit 'result' field, else try str(out)
        if isinstance(out, dict) and out.get("result"):
            txt = str(out.get("result"))
        else:
            txt = str(out)
        tool_texts.append(txt)
        tool_nums.extend(_extract_numbers(txt))

    # simple numeric mismatch detection: draft numbers not appearing in any tool output
    mismatches = []
    for n in draft_nums:
        if n not in tool_nums:
            mismatches.append(n)

    if mismatches:
        notes.append(f"أرقام في النص ({', '.join(mismatches)}) لم تظهر في مخرجات الأدوات.")
        corrections["missing_numbers_in_tools"] = mismatches

    # simple unit token check: if draft mentions a unit but tools do not
    draft_units = [u for u in UNIT_TOKENS if (f" {u}" in draft_text or f"{u} " in draft_text or draft_text.endswith(u))]
    if draft_units:
        tool_units = [u for u in UNIT_TOKENS if any(u in tt for tt in tool_texts)]
        for u in draft_units:
            if u not in tool_units:
                notes.append(f"الوحدة '{u}' مذكورة في الإجابة لكن لم تُذكر في مخرجات الأدوات.")
                corrections.setdefault("missing_units_in_tools", []).append(u)

    passed = len(notes) == 0
    return {"passed": passed, "notes": notes, "corrections": corrections}


def consistency_checker(tool_outputs: Iterable[Dict[str, Any]], draft_text: str) -> Dict[str, Any]:
    """Check high-level consistency: claims in draft should be supported by tool outputs.

    Very lightweight heuristics:
    - numbers in draft should appear in tool outputs (covered partly above)
    - if draft uses causal language (لأن، بسبب، نتيجةً لِـ) ensure a causal tool was present
    - check that assertions from tool outputs are not contradicted by the draft (naive substring check)
    """
    notes: List[str] = []
    tool_texts = [str((t.get("out") or {}).get("result") or t.get("out") or "") for t in tool_outputs]

    # detect causal claim in draft
    causal_tokens = ["لأن", "بسبب", "نتيجة", "بالتالي", "مما أدى"]
    if any(tok in draft_text for tok in causal_tokens):
        # ensure a causal tool ran
        has_causal = any(t.get("tool") == "causal.infer" or (isinstance(t.get("tool"), str) and "causal" in t.get("tool")) for t in tool_outputs)
        if not has_causal:
            notes.append("يوجد استدلال سببي في النص لكن لم تُنفّذ أداة استنتاج سببي للتحقق.")

    # check for contradictions: if a tool output contains phrase X and draft contains 'ليس X' or 'لا X'
    for tt in tool_texts:
        if not tt:
            continue
        snippet = tt.strip()
        if len(snippet) < 6:
            continue
        # naive contradiction detection
        if ("ليس " + snippet) in draft_text or ("لا " + snippet) in draft_text:
            notes.append(f"النص قد يتناقض مع مخرجات الأداة: '{snippet[:40]}...'")

    passed = len(notes) == 0
    return {"passed": passed, "notes": notes}


def safety_gate(toolrunner, draft_text: str) -> Dict[str, Any]:
    """Run a safety gate. If toolrunner provides safety.review, prefer that.

    Returns {passed: bool, notes: [...], rollback: bool} -- rollback=True indicates
    an emergency block should be applied if the content is disallowed.
    """
    notes: List[str] = []
    rollback = False

    if toolrunner and "safety.review" in toolrunner.available():
        try:
            r = toolrunner.run("safety.review", {"text": draft_text})
            # expected r to contain {'ok': True, 'passed': bool, 'flags': [...]} or similar
            if r.get("ok"):
                passed = r.get("passed", True)
                flags = r.get("flags") or []
                notes.extend(flags)
                if not passed:
                    rollback = True
                return {"passed": passed, "notes": notes, "rollback": rollback}
            else:
                notes.append("فشل تنفيذ أداة فحص السلامة (tool error)")
                # conservative: fail-safe
                return {"passed": False, "notes": notes, "rollback": True}
        except Exception as e:
            notes.append(f"استثناء أثناء فحص السلامة: {e}")
            return {"passed": False, "notes": notes, "rollback": True}

    # fallback heuristics: simple banned-word scan (conservative)
    banned = ["انتحار", "تفجير", "قنبلة", "تسريب بيانات", "تعذيب"]
    lower = (draft_text or "").lower()
    found = [b for b in banned if b in lower]
    if found:
        notes.append(f"محتوى محظور كشف: {', '.join(found)}")
        return {"passed": False, "notes": notes, "rollback": True}

    return {"passed": True, "notes": [] , "rollback": False}


def perform_tri_verify(tool_outputs: Iterable[Dict[str, Any]], draft_text: str, toolrunner=None) -> Dict[str, Any]:
    """Run the three verification checks and return an aggregated report.

    Returned shape:
    {
      'units_math': {..},
      'consistency': {..},
      'safety': {..},
      'passed': bool
    }
    """
    u = units_math_checker(tool_outputs, draft_text)
    c = consistency_checker(tool_outputs, draft_text)
    s = safety_gate(toolrunner, draft_text)

    passed = all([u.get("passed", False), c.get("passed", False), s.get("passed", False)])
    return {"units_math": u, "consistency": c, "safety": s, "passed": passed}
