"""Micro Planner (improved deterministic)
Generates a deterministic micro-plan from a prompt and writes it to the ConsciousBridge.

Improvement: surface salient task tokens inside the *step texts* so plans are grounded.
"""
from __future__ import annotations

import re
from typing import Dict, Any, List

try:
    from agl.lib.core_memory.bridge_singleton import get_bridge
except ImportError:
    def get_bridge():
        return None


_STOP = {
    # Arabic
    "اكتب", "خطة", "من", "خطوات", "ل", "لعمل", "عمل", "على", "في", "مع", "ملف", "ملفات", "مشروع",
    "الى", "إلى", "عن", "ثم",
    # English
    "write", "plan", "steps", "for", "with", "and", "the", "a", "an",
}


def _salient_tokens(task: str, *, max_tokens: int = 3) -> List[str]:
    t = (task or "").strip()
    if not t:
        return []
    # keep Arabic/latin/numbers
    words = re.findall(r"[A-Za-z0-9_]+|[؀-ۿ]+", t)
    out: List[str] = []
    for w in words:
        w0 = w.strip().lower()
        if not w0 or w0 in _STOP:
            continue
        if len(w0) < 3:
            continue
        if w0 not in out:
            out.append(w0)
        if len(out) >= max_tokens:
            break
    return out


class MicroPlanner:
    name = "Plan_and_Execute_MicroPlanner"

    def process_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        task = payload.get('task') or payload.get('prompt') or payload.get('query') or payload.get('text') or ''
        toks = _salient_tokens(str(task), max_tokens=3)
        anchor = " ".join(toks) if toks else "المهمة"

        steps = [
            f"1) تحديد الهدف وجمع المتطلبات (مرتكزات: {anchor})",
            f"2) اختيار طريقة التنفيذ والأداة المناسبة ({anchor})",
            f"3) تنفيذ النسخة الأولية ثم التحقق والتوثيق ({anchor})",
            "4) اختبار تجريبي لمجموعة صغيرة",
            "5) قياس النتائج وضبط المعلمات",
            "6) نشر تدريجي ومراقبة",
        ]
        plan = {'title': f'خطة تنفيذ قصيرة لـ: {str(task)[:60]}', 'steps': steps}
        out = {"ok": True, "engine": self.name, "plan": plan, 'text': '؛ '.join(steps)}

        try:
            br = get_bridge()
            if br is not None:
                trace = payload.get('trace_id') if isinstance(payload, dict) else None
                pid = br.put('plan', {'plan': plan, 'text': out.get('text')}, trace_id=trace)
                if trace:
                    try:
                        pps = br.query_by_trace_and_type(trace, 'prompt_plan', scope='stm')
                        if pps:
                            br.link(pps[-1]['id'], pid, 'expanded_into_plan')
                    except Exception:
                        pps = [e for e in br.query(trace_id=trace, scope='stm') if e.get('type') == 'prompt_plan']
                        if pps:
                            br.link(pps[-1]['id'], pid, 'expanded_into_plan')
        except Exception:
            pass

        return out


def factory():
    return MicroPlanner()

