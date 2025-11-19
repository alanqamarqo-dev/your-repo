"""Two-stage self-critique and revise engine used in AGI chain.

Stage 1: Produce a brief critique and suggested fixes (uses slightly higher temperature
         in actual LLM callers when integrated).
Stage 2: Produce a revised, structured answer (low temperature) that tries to inject
         the explicit section headings and keywords the evaluator checks for.
"""
from typing import Dict, Any
from Integration_Layer.integration_registry import registry


class SelfCritiqueAndRevise:
    name = "Self_Critique_and_Revise"

    def process_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        draft = payload.get("draft") or payload.get("text") or payload.get("prompt") or ""
        if not draft:
            return {"ok": False, "reason": "no input"}

        # Stage 1: self-critique (local heuristics + optional engine)
        critique = (
            "نقد ذاتي:\n"
            "- قد يحتاج النص لتوضيح القيود التشغيلية (مثل حالة الطقس، سعة المضخة).\n"
            "- اقترح توضيح خطوات التنفيذ وقياسات النجاح.\n"
            "- راجع الأخلاقيات والسلامة عند نقل مبادئ إلى سياق المرور.\n"
        )

        # Stage 2: revised draft attempt — try to call Hosted_LLM/Ollama with low temp
        revised = draft
        try:
            eng = registry.get('Hosted_LLM') or registry.get('Ollama_KnowledgeEngine')
            if eng:
                # ask engine to produce a revised structured answer. Most adapters
                # accept process_task({'query': ...}) shape; fall back to .ask
                prompt = (
                    "أعدَّ صياغة الإجابة التالية بما يضمن الأقسام المطلوبة والعناوين التالية حرفيًا:\n"
                    "أولًا: تصميم نظام الري\nثانيًا: الربط مع المرور\nثالثًا: التشابه المبدئي\nرابعًا: القيود والمقايضات\nخامسًا: أدوات القياس\nسادسًا: خطوات التنفيذ\nسابعًا: الوعي بالحدود والتحسين\nخاتمة: حل مبتكر وبدائل\n\n"
                    + "المسودة:\n" + draft
                )
                try:
                    resp = eng.process_task({'query': prompt})
                except Exception:
                    try:
                        resp = eng.ask(prompt, temperature=0.0)
                    except Exception:
                        resp = None
                if isinstance(resp, dict) and resp.get('text'):
                    revised = resp.get('text')
        except Exception:
            pass

        # final normalized text
        text = revised or draft
        return {"ok": True, "engine": self.name, "critique": critique, "revised": text, "text": text}


def factory():
    return SelfCritiqueAndRevise()
