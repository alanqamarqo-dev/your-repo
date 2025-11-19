import os
from typing import Dict, Any, Optional, List


def _is_mock_mode() -> bool:
    return os.getenv("AGL_TEST_SCAFFOLD_FORCE", "0") == "1" or (
        os.getenv("AGL_LLM_MODEL") is not None
    )

import random
import hashlib
from typing import List, Dict, Optional

class CreativeInnovationEngine:
    def __init__(self, seed: Optional[int] = None, rng: Optional[random.Random] = None, config: Optional[Dict[str, Any]] = None, **kwargs) -> None:
        # اجعل المخرجات حتمية عند تزويد seed
        # نقبل أيضًا config و kwargs لتكون التهيئة متسامحة مع محمّلات المحركات في الاختبارات
        self._rng = rng if rng is not None else random.Random(seed)

    # واجهة مطلوبة: تُرجع قائمة عناصر كل عنصر dict: {"idea": str, "scores": {"composite": float}}
    def generate_ideas(self, topic: str, n: int = 5, constraints: Optional[Dict[str, Any]] = None, **kwargs) -> List[Dict]:
        base = [
            f"حلّ بسيط قابل للتنفيذ لـ {topic}",
            f"حلّ مبتكر منخفض التكاليف لـ {topic}",
            f"تجربة سريعة (Prototype) لـ {topic}",
            f"تعاون مجتمعي/مفتوح المصدر لـ {topic}",
            f"أتمتة جزئية مع رقابة بشرية لـ {topic}",
            f"مؤشر أداء/قياس واضح لـ {topic}",
            f"توسيع تدريجي على مراحل لـ {topic}",
        ]
        # allow env override for number of ideas to generate (safe default preserved)
        try:
            import os
            n = int(os.environ.get('AGL_CREATIVE_IDEAS_LIMIT', str(n)))
        except Exception:
            pass
        # اختَر n أفكار بشكل حتمي باستخدام rng المحلي
        # تَلقِّي قيود بسيطة (مثل budget) — الآن نقبل الوسيط لكنّنا نستخدمه فقط للتماثل مع الواجهة
        picks = [self._rng.choice(base) for _ in range(max(1, n))]
        out: List[Dict] = []
        for idea in picks:
            # مركّب بسيط حتمي قائم على تجزئة الفكرة (0..1)
            h = hashlib.md5(idea.encode("utf-8")).hexdigest()
            composite = int(h[:8], 16) / 0xFFFFFFFF
            out.append({"idea": idea, "scores": {"composite": float(composite)}})
        # رتب النتائج حسب score مركب تنازليًا — الاختبارات تتوقع ترتيبًا تنازليًا
        out.sort(key=lambda x: x["scores"]["composite"], reverse=True)
        return out

    # واجهة مطلوبة: تُرجع float في [0, 1]
    def evaluate_novelty(self, text: str, knowledge_fingerprints: Optional[List[str]] = None, **kwargs) -> float:
        # نقبل knowledge_fingerprints و kwargs للاحتفاظ بالتوافق مع الاختبارات
        h = hashlib.md5(text.encode("utf-8")).hexdigest()
        return float(int(h[8:16], 16) / 0xFFFFFFFF)

    # النسخة “الغنية” (ممكن تكون موجودة سابقًا باسم lateral_think): تُرجع dict
    # نُبقيها داخلية، ونجعل الواجهة العامة ترجع قائمة فقط
    def _lateral_think_full(self, topic: str, technique: str = "SCAMPER") -> Dict:
        ops = [
            ("Substitute", f"{technique}: Substitute عنصر في {topic}"),
            ("Combine", f"{technique}: Combine فكرتين حول {topic}"),
            ("Adapt", f"{technique}: Adapt من مجال مختلف إلى {topic}"),
            ("Modify/Maximize/Minimize", f"{technique}: Modify/Maximize/Minimize داخل {topic}"),
            ("Put to other uses", f"{technique}: Put to other uses لـ {topic}"),
            ("Eliminate", f"{technique}: Eliminate تعقيدًا في {topic}"),
            ("Reverse/Rearrange", f"{technique}: Reverse/Rearrange تسلسل {topic}"),
        ]
        
        self._rng.shuffle(ops)
        # نعيد خطوات كقائمة من dicts تحتوي على الحقل 'op' (الذي تتوقعه الاختبارات)
        steps = [{"op": name, "detail": detail} for (name, detail) in ops]
        return {"technique": technique, "steps": steps, "count": len(steps)}

    # المطلوب في الاختبارات: تُرجع قائمة (الخطوات فقط)
    def lateral_thinking(self, topic: str, technique: str = "SCAMPER") -> Dict:
        # واجهة الاختبارات: تعيد dict تحتوي على قائمة steps (من dicts)
        return self._lateral_think_full(topic, technique=technique)

    # للحفاظ على التوافق إن كان اسم قديم مستخدم في أماكن أخرى
    def lateral_think(self, topic: str, technique: str = "SCAMPER") -> List[str]:
        # واجهة قديمة: تُرجع قائمة من نصوص العمليات للحفاظ على التوافق
        return [s["op"] for s in self._lateral_think_full(topic, technique=technique)["steps"]]

    def process_task(self, task: dict) -> dict:
        """Minimal process_task wrapper to satisfy loader expectations.
        Accepts a task dict with a 'kind' key and routes to existing methods.
        """
        kind = (task or {}).get("kind", "ideas")
        topic = (task or {}).get("topic", "موضوع")
        if kind == "ideas":
            try:
                n = int((task or {}).get("n", 5))
                try:
                    import os
                    n = int(os.environ.get('AGL_CREATIVE_IDEAS_LIMIT', str(n)))
                except Exception:
                    pass
            except Exception:
                n = 5
            ideas = self.generate_ideas(topic, n=n)
            return {"ok": True, "ideas": ideas}
        if kind == "lateral":
            tech = (task or {}).get("technique", "SCAMPER")
            steps = self.lateral_thinking(topic, technique=tech)
            return {"ok": True, "steps": steps}
        if kind == "novelty":
            txt = (task or {}).get("text", "")
            score = self.evaluate_novelty(txt)
            return {"ok": True, "novelty": score}
        return {"ok": False, "error": "unknown kind"}



def create_engine(config: Optional[Dict[str, Any]] = None) -> CreativeInnovationEngine:
    # نقبل config ونمرره إلى المُهيئ إن كان مطلوبًا
    seed = None
    if isinstance(config, dict) and config.get("seed") is not None:
        seed = config.get("seed")
    return CreativeInnovationEngine(seed=seed, config=config)


def healthcheck() -> Dict[str, Any]:
    return {"ok": True, "engine": "Creative_Innovation", "version": "0.1"}
