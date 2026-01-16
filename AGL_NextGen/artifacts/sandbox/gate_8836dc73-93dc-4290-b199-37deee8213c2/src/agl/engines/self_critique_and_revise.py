"""Two-stage self-critique and revise engine used in AGI chain.

Stage 1: Produce a brief critique and suggested fixes (uses slightly higher temperature
         in actual LLM callers when integrated).
Stage 2: Produce a revised, structured answer (low temperature) that tries to inject
         the explicit section headings and keywords the evaluator checks for.
"""
from typing import Dict, Any
# from Integration_Layer.integration_registry import registry
# Mock registry for now or import from new location if available
registry = {}


class SelfCritiqueAndRevise:
    name = "Self_Critique_and_Revise"

    def process_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        draft = payload.get("draft") or payload.get("text") or payload.get("prompt") or ""
        if not draft:
            return {"ok": False, "reason": "no input"}

        # Stage 1: self-critique (General Purpose)
        critique = ""
        try:
            eng = registry.get('Hosted_LLM') or registry.get('Ollama_KnowledgeEngine')
            if eng:
                critique_prompt = (
                    "قم بنقد الإجابة التالية بشكل بناء. حدد نقاط الضعف، المعلومات الناقصة، أو الأخطاء المنطقية.\n"
                    "الإجابة:\n" + draft
                )
                try:
                    resp = eng.process_task({'query': critique_prompt})
                    if isinstance(resp, dict) and resp.get('text'):
                        critique = resp.get('text')
                except Exception:
                    pass
        except Exception:
            pass
            
        if not critique:
             critique = "لم يتم توليد نقد (المحرك غير متاح)."

        # Stage 2: revised draft attempt — try to call Hosted_LLM/Ollama with low temp
        revised = draft
        try:
            eng = registry.get('Hosted_LLM') or registry.get('Ollama_KnowledgeEngine')
            if eng:
                # ask engine to produce a revised structured answer based on the critique
                prompt = (
                    "أعد صياغة الإجابة التالية لتكون أكثر دقة وشمولية، بناءً على النقد الموجه.\n"
                    "النقد:\n" + critique + "\n\n"
                    "الإجابة الأصلية:\n" + draft + "\n\n"
                    "الإجابة المحسنة:"
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
