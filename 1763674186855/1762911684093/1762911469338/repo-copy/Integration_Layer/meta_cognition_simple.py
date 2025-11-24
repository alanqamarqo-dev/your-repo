import os
import json
import re
from typing import Any

try:
    # reuse the Ollama http/cli helpers if available
    from Integration_Layer.rag_adapter_ollama import _ollama_http, _ollama_cli
except Exception:
    _ollama_http = None
    _ollama_cli = None


class SimpleMetaEvaluator:
    """A tiny meta-cognition evaluator that uses the same local Ollama LLM.

    It returns {'score': float(0..1), 'notes': str}.
    """

    def __init__(self, base_url: str | None = None, model: str | None = None, timeout: int = 20):
        self.base_url = base_url or os.getenv('AGL_LLM_BASEURL') or os.getenv('OLLAMA_API_URL')
        self.model = model or os.getenv('AGL_LLM_MODEL')
        self.timeout = timeout

    def evaluate(self, plan: Any) -> dict:
        # plan may be dict or str
        text = plan
        if isinstance(plan, dict):
            try:
                text = json.dumps(plan, ensure_ascii=False, indent=2)
            except Exception:
                text = str(plan)

        prompt = (
            "قيّم الخطة أو الإجابة التالية وفق ثلاثة معايير: وضوح الخطة، الاستشهاد بالمصادر، والسلامة. "
            "أعط درجة من 0 إلى 1 بدقة (مثال: 0.87) واطرح ملاحظات قصيرة باللغة العربية. "
            "أعد النتيجة بصيغة JSON فقط: {\"score\": 0.87, \"notes\": \"...\"}.\n\n"
            "محتوى للتقييم:\n" + str(text)
        )

        # tuning for evaluator: small generation, low temperature
        num_predict = int(os.getenv('AGL_META_NUM_PREDICT') or 64)
        num_ctx = int(os.getenv('AGL_META_NUM_CTX') or 1024)
        temp = float(os.getenv('AGL_META_TEMPERATURE') or 0.0)
        keep_alive = os.getenv('AGL_LLM_KEEP_ALIVE') or '1m'

        # prefer HTTP path
        try:
            if _ollama_http and self.base_url and self.model:
                txt = _ollama_http(prompt, self.base_url, self.model, self.timeout,
                                   num_predict=num_predict, num_ctx=num_ctx, temperature=temp,
                                   keep_alive=keep_alive, stream=False)
            elif _ollama_cli and self.model:
                txt = _ollama_cli(prompt, self.model, self.timeout)
            else:
                return {'score': 0.5, 'notes': 'no-llm-available'}
        except Exception as e:
            return {'score': 0.5, 'notes': f'error: {e}'}

        # attempt to parse JSON from model output
        try:
            parsed = json.loads(txt)
            score = float(parsed.get('score', 0.5)) if isinstance(parsed, dict) else 0.5
            notes = parsed.get('notes', '') if isinstance(parsed, dict) else str(parsed)
            return {'score': max(0.0, min(1.0, float(score))), 'notes': str(notes)}
        except Exception:
            # try to extract a floating number
            m = re.search(r"([01](?:\.\d+))", txt)
            if m:
                try:
                    sc = float(m.group(1))
                    sc = max(0.0, min(1.0, sc))
                except Exception:
                    sc = 0.5
            else:
                sc = 0.5
            # use first 300 chars as notes
            return {'score': sc, 'notes': txt[:300]}


def meta_evaluate(plan: Any) -> dict:
    evaluator = SimpleMetaEvaluator()
    return evaluator.evaluate(plan)
