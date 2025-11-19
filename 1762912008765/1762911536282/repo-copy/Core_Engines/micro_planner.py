"""Micro Planner (stub)
Generates a deterministic micro-plan from a prompt and writes it to the ConsciousBridge.
"""
from typing import Dict, Any
from Core_Memory.bridge_singleton import get_bridge


class MicroPlanner:
    name = "Plan_and_Execute_MicroPlanner"

    def process_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # Create a deterministic plan based on the provided text/task
        task = payload.get('task') or payload.get('prompt') or payload.get('query') or payload.get('text') or ''
        # Simple step breakdown (deterministic)
        steps = [
            "1) تقييم المتطلبات وجمع البيانات الأساسية",
            "2) تصميم مبدئي للنموذج/المسار",
            "3) تحديد نقاط الاختناق وعتبات الأداء",
            "4) اختبار تجريبي لمجموعة صغيرة",
            "5) قياس النتائج وضبط المعلمات",
            "6) نشر تدريجي ومراقبة",
        ]
        plan = {'title': f'خطة تنفيذ قصيرة لـ: {task[:60]}', 'steps': steps}
        out = {"ok": True, "engine": self.name, "plan": plan, 'text': '؛ '.join(steps)}

        # Persist plan to the ConsciousBridge and link to previous prompt_plan
        try:
            br = get_bridge()
            trace = payload.get('trace_id') if isinstance(payload, dict) else None
            pid = br.put('plan', {'plan': plan, 'text': out.get('text')}, trace_id=trace)
            if trace:
                try:
                    pps = br.query_by_trace_and_type(trace, 'prompt_plan', scope = 'stm')
                    if pps:
                        br.link(pps[-1]['id'], pid, 'expanded_into_plan')
                except Exception:
                    # fallback to previous behavior if helper missing
                    pps = [e for e in br.query(trace_id=trace, scope='stm') if e.get('type') == 'prompt_plan']
                    if pps:
                        br.link(pps[-1]['id'], pid, 'expanded_into_plan')
        except Exception:
            pass

        return out


def factory():
    return MicroPlanner()
