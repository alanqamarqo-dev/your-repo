from __future__ import annotations
from typing import Any, Dict, List, Optional
import logging
import os

# Hypothesis generator knob (module-level)
try:
    _AGL_HYPOTHESIS_TOP_N = int(os.environ.get('AGL_HYPOTHESIS_TOP_N', '3'))
except Exception:
    _AGL_HYPOTHESIS_TOP_N = 3

logger = logging.getLogger("AGL.Hypothesis_Generator")
if not logger.handlers:
    import sys
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(h)
logger.setLevel(logging.INFO)

# استدعاء اختياري للـLLM عبر Hosted_LLM إن توفر
try:
    from Core_Engines.Hosted_LLM import chat_llm
except Exception:
    chat_llm = None  # بيئات CI بدون مزودات

_MOCK_ON = os.getenv("AGL_OLLAMA_KB_MOCK", "0") in ("1", "true", "True") or \
           os.getenv("AGL_EXTERNAL_INFO_MOCK", "0") in ("1", "true", "True")

class HypothesisGeneratorEngine:
    """
    يولّد فرضيات مرتبة حول ظاهرة/نص/بيانات.
    واجهة محرك موحّدة: name + process_task(payload)->Dict
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.name = "HYPOTHESIS_GENERATOR"
        self.config = config or {}

    def _llm_hypothesize(self, topic: str, context: str) -> List[str]:
        if chat_llm is None:
            return []
        # prompt مختصر، يمكنك لاحقاً استبداله بـ Hybrid_Composer لو أردت
        sys_msg = "أنت باحث علمي يولّد فرضيات قابلة للاختبار بالعربية المعيارية."
        user_msg = f"الموضوع: {topic}\nالسياق:\n{context}\n" \
                   f"أعطني 3 فرضيات مختصرة وقابلة للاختبار، مرقّمة."
        try:
            text = chat_llm(system_message=sys_msg, user_message=user_msg) or "" # type: ignore
            # محاولة بسيطة لاستخراج عناصر مرقّمة
            lines = [l.strip("- ").strip() for l in text.splitlines() if l.strip()]
            hyps = [l for l in lines if any(l.startswith(x) for x in ("1", "2", "3", "١", "٢", "٣"))]
            try:
                _AGL_HYPOTHESIS_TOP_N = int(os.environ.get('AGL_HYPOTHESIS_TOP_N', '3'))
            except Exception:
                _AGL_HYPOTHESIS_TOP_N = 3
            return hyps[:_AGL_HYPOTHESIS_TOP_N] if hyps else lines[:_AGL_HYPOTHESIS_TOP_N]
        except Exception as e:
            logger.debug("LLM hypothesis call failed: %r", e)
            return []

    def process_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        topic = (payload or {}).get("topic", "") or "موضوع عام"
        context = (payload or {}).get("context", "") or ""
        hints = (payload or {}).get("hints", []) or []

        # 1) جرّب LLM إن متاح
        hyps = self._llm_hypothesize(topic, context)

        # 2) إن لم يتوفر LLM أو عاد فارغًا: استخدم توليد مبسّط/مقعّد + تلميحات
        if not hyps:
            base = [
                f"إذا تغيّر {topic} بنسبة صغيرة، فسيظهر أثر قابل للقياس في سياق {context[:60]}…",
                f"العلاقة بين {topic} وبعض العوامل قد تكون غير خطيّة ويمكن نمذجتها بملاءمة أسيّة.",
                f"يمكن إعادة اختبار فرضيات قديمة حول {topic} ببيانات أحدث للتحقق من الاستقرار الزمني."
            ]
            if hints:
                base.append(f"استنادًا إلى أدلة: {', '.join(map(str, hints[:3]))}…")
            try:
                _AGL_HYPOTHESIS_TOP_N = int(os.environ.get('AGL_HYPOTHESIS_TOP_N', '3'))
            except Exception:
                _AGL_HYPOTHESIS_TOP_N = 3
            hyps = base[:_AGL_HYPOTHESIS_TOP_N]

        return {
            "engine": self.name,
            "hypotheses": hyps,
            "count": len(hyps),
            "confidence": 0.6 if hyps else 0.0
        }

def create_engine(config: Optional[Dict[str, Any]] = None) -> HypothesisGeneratorEngine:
    return HypothesisGeneratorEngine(config=config)
from typing import List, Dict
import itertools
import uuid


class HypothesisGenerator:
    """Generate simple hypotheses from accepted facts.

    This is a lightweight, extensible generator. Later we can plug LLM prompts
    or template-based generators per-domain.
    """

    def __init__(self, max_pairs: int = 50, max_hyps: int = 20):
        self.max_pairs = max_pairs
        self.max_hyps = max_hyps

    def propose(self, facts: List[Dict]) -> List[Dict]:
        hyps = []
        # Take last N facts to reduce combinatoric blowup
        pool = facts[-self.max_pairs:]
        for a, b in itertools.combinations(pool, 2):
            if (a.get('domain') or '').strip() != (b.get('domain') or '').strip():
                continue
            aid = a.get('id') or a.get('ts')
            bid = b.get('id') or b.get('ts')
            text_a = (a.get('text') or '')[:80]
            text_b = (b.get('text') or '')[:80]
            hyp = {
                'id': uuid.uuid4().hex,
                'domain': a.get('domain'),
                'hypothesis': f"قد ترتبط '{text_a}' مع '{text_b}' بمعنى أن وجود أحدهما قد يؤثر على الآخر.",
                'support': [aid, bid],
                'confidence': 0.55
            }
            hyps.append(hyp)
        hyps.sort(key=lambda x: x.get('confidence', 0.0), reverse=True)
        return hyps[: self.max_hyps]
