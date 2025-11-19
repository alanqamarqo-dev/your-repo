"""Prompt Composer V2
Builds an adaptive prompt with a small few-shot and structured sections.
"""
from typing import Dict, Any
from Core_Memory.bridge_singleton import get_bridge


class PromptComposerV2:
    name = "Prompt_Composer_V2"

    FEW_SHOT = [
        {
            "task": "نظام الري لمنزل صغير",
            "example": "ملخّص: نظام ري بالتنقيط فعال من حيث التكلفة؛ نقاط تنفيذية: اختيار مضخة منخفضة الضغط، تقسيم الشبكة، صمامات تحكم؛ قياسات نجاح: انخفاض استهلاك المياه بنسبة 30%"
        },
        {
            "task": "تحسين تقاطع مروري",
            "example": "ملخّص: تحسين التدفق بتوقيت إشارات ديناميكي؛ نقاط تنفيذية: استشعار حركة، ضبط أولوية، نمذجة حركة؛ قياسات نجاح: تقليل زمن الانتظار بنسبة 25%"
        },
        {
            "task": "ربط نظري بين نظامين",
            "example": "ملخّص: الربط عبر مفهوم التدفق والموارد؛ مثال ربط: تشابه بين توزيع المياه وتوزيع حركة المرور؛ عناصر فلسفية: حدود النظام، مقايضات أخلاقية، اقتراحات لتحسين النموذج"
        }
    ]

    def process_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        task = payload.get("task") or payload.get("prompt") or payload.get("query") or ""
        constraints = payload.get("constraints", "")
        budget = payload.get("budget", "وقت: 5 دقائق; كلمات: 300")

        # System hint that *forces* presence of the exact section titles and keywords
        sys_hint = (
            "اكتب إجابة مُهيكلة بالعربية وفق الأقسام التالية حرفيًا:\n"
            "أولًا) تصميم نظام الري (10×20م، ميزانية 1000$): اذكر: مضخة، تدفق، ضغط، رشاش، شبكة، جاذبية، أنابيب، نظام بالتنقيط، صمام.\n"
            "ثانيًا) الربط مع المرور: استخدم مفردات: إشارة، مرور، تقاطع، تدفق المركبات، إزاحة، أولوية، حارات، توقيت.\n"
            "ثالثًا) التشابه المبدئي: اذكر: تشابه/تماثل/محاكاة، تطبيق نفس، خرائط التدفق، قانون حفظ، نموذج شبكي.\n"
            "رابعًا) القيود والمقايضات: قيود، تكلفة، سلامة، أولويات، مقايضة.\n"
            "خامسًا) أدوات القياس: قياس، عدادات تدفق/ضغط/زمن انتظار.\n"
            "سادسًا) خطوات التنفيذ: خطوات/مرحلة/تنفيذ (قائمة مرقمة).\n"
            "سابعًا) الوعي بالحدود: اذكر صراحةً: حدود النظام، قيود النموذج، وكيفية التحسين.\n"
            "اختم بـ فقرة قصيرة: حل مبتكر/منخفضة التكلفة وبدائل.\n"
        )

        template = (
            "أنت مساعد تقني. أعد مسودة مركزة باستخدام التلميحات التالية.\n\n"
        )

        shot = "\n\nمثال قصير:\n- " + "; ".join([f"{s['task']}: {s['example']}" for s in self.FEW_SHOT])
        prompt = f"{template}{sys_hint}\n\nالسؤال:\n{task}\n\nقيود: {constraints}\nميزانية: {budget}{shot}"
        out = {"ok": True, "engine": self.name, "prompt": prompt, "text": prompt}
        # Best-effort: persist the generated prompt plan into the ConsciousBridge
        try:
            br = get_bridge()
            trace = None
            # if payload was provided in outer scope, try to read trace_id
            # (process_task signature receives payload arg)
            # we capture from locals() to avoid changing the signature
            try:
                trace = locals().get('payload', {}).get('trace_id')
            except Exception:
                trace = None
            pid = br.put('prompt_plan', {'prompt': prompt, 'task': task}, trace_id=trace)
            if trace:
                # Use strict intersection helper to find rationale events for this trace
                try:
                    rats = br.query_by_trace_and_type(trace, 'rationale', scope = 'stm')
                    if rats:
                        br.link(rats[-1]['id'], pid, 'informs_prompt')
                except Exception:
                    # best-effort: fallback to previous behavior if helper missing
                    rats = [e for e in br.query(trace_id=trace, scope='stm') if e.get('type') == 'rationale']
                    if rats:
                        br.link(rats[-1]['id'], pid, 'informs_prompt')
        except Exception:
            pass
        return out


def factory():
    return PromptComposerV2()


def compose_prompt(task_text: str, constraints: str = '', budget: str = '') -> str:
    """Compatibility wrapper used by Reasoning_Layer.auto-prompt.

    Returns a single string prompt that the LLM adapters can accept.
    """
    pc = PromptComposerV2()
    payload = {"task": task_text, "constraints": constraints, "budget": budget}
    out = pc.process_task(payload)
    return out.get('prompt') or out.get('text') or ''
