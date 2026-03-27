import json
import os
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Dict, List, Optional

# المسار الافتراضي لتخزين الذاكرة الاستراتيجية
def _default_path() -> Path:
    base = Path(__file__).resolve().parents[1]
    return base / "artifacts" / "strategic_memory.jsonl"


@dataclass
class MemoryItem:
    ts: float
    task_title: str
    task_type: str
    domain: str
    strategy: Dict[str, Any] = field(default_factory=dict)
    score: Optional[float] = None
    success: Optional[bool] = None
    meta: Dict[str, Any] = field(default_factory=dict)


class StrategicMemory:
    """
    ذاكرة استراتيجية متقدمة:
    - تخزن نتائج المهام السابقة (عنوان، نوع، دومين، نجاح/فشل، سكورات، استراتيجية).
    - تسترجع مهام مشابهة للمهمة الحالية.
    - تبني "بروفايل" للدومينات (medical/math/project/...).
    - تقترح استراتيجية مناسبة لكل مهمة جديدة.
    """

    def __init__(self, path: Optional[Path] = None, max_items: int = 2000) -> None:
        self.path: Path = Path(path or _default_path())
        self.max_items = max_items
        self.items: List[MemoryItem] = []
        self._loaded: bool = False

    # ---------- IO & تحميل ----------
    def _ensure_dir(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> None:
        if self._loaded:
            return
        self.items = []
        if self.path.exists():
            with self.path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except Exception:
                        continue
                    self.items.append(
                        MemoryItem(
                            ts=data.get("ts", data.get("timestamp", time.time())),
                            task_title=data.get("task_title", ""),
                            task_type=data.get("task_type", "unknown"),
                            domain=data.get("domain", "generic"),
                            strategy=data.get("strategy", {}) or {},
                            score=data.get("score"),
                            success=data.get("success"),
                            meta=data.get("meta", {}) or {},
                        )
                    )
        self._loaded = True

    def append(self, item: MemoryItem) -> None:
        self.load()
        self.items.append(item)
        if len(self.items) > self.max_items:
            self.items = self.items[-self.max_items :]
        self._ensure_dir()
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(item), ensure_ascii=False) + "\n")

    # ---------- تشابه و استرجاع ----------
    def _similarity(
        self, item: MemoryItem, title: str, domain: str, task_type: str
    ) -> float:
        score = 0.0
        title = title or ""
        if item.task_type == task_type:
            score += 0.3
        if item.domain == domain:
            score += 0.3
        a_tokens = set((item.task_title or "").split())
        q_tokens = set(title.split())
        if a_tokens and q_tokens:
            overlap = len(a_tokens & q_tokens) / max(1, len(q_tokens))
            score += 0.4 * overlap
        return score

    def recall_relevant(
        self, title: str, domain: str, task_type: str, k: int = 5
    ) -> List[MemoryItem]:
        self.load()
        scored: List[Any] = [
            (self._similarity(it, title, domain, task_type), it) for it in self.items
        ]
        scored = [x for x in scored if x[0] > 0.0]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [it for _, it in scored[:k]]

    # ---------- استنتاج الدومين و البروفايل ----------
    def infer_domain(self, task_type: str, title: str) -> str:
        t = (title or "").lower()
        # دومين طبي
        if any(
            key in t
            for key in [
                "ضغط الدم",
                "الضغط",
                "السكري",
                "الإنفلونزا",
                "الانفلونزا",
                "كلوي",
                "كلية",
                "دواء",
                "الأدوية",
                "ادوية",
                "pharma",
                "medical",
                "مضاد",
                "مضادات",
                "مضادات الحيوية",
                "المضادات",
            ]
        ):
            return "medical"
        # دومين رياضي/تحليلي
        if any(
            key in t
            for key in [
                "تكامل",
                "تفاضل",
                "خوارزم",
                "مصفوف",
                "مصفوفة",
                "معادلة",
                "جبر",
                "احتمال",
                "احتمالات",
                "رياض",
                "algebra",
                "matrix",
            ]
        ):
            return "math"
        # مشاريع
        if any(key in t for key in ["مشروع", "project", "plan", "خطة"]):
            return "project"
        # افتراضي
        return f"general_{task_type or 'unknown'}"

    def summarize_profile(self) -> Dict[str, Dict[str, Any]]:
        """
        يعيد: { "medical": {"count":.., "success_rate":.., "avg_score":..}, ... }
        """
        self.load()
        by_domain: Dict[str, Dict[str, Any]] = {}
        for it in self.items:
            dom = it.domain or "unknown"
            dom_stats = by_domain.setdefault(
                dom, {"count": 0, "success": 0, "score_sum": 0.0, "scored": 0}
            )
            dom_stats["count"] += 1
            if it.success:
                dom_stats["success"] += 1
            if it.score is not None:
                dom_stats["score_sum"] += float(it.score)
                dom_stats["scored"] += 1
        for dom, st in by_domain.items():
            c = st["count"] or 1
            st["success_rate"] = st["success"] / c
            st["avg_score"] = (
                st["score_sum"] / st["scored"] if st["scored"] > 0 else 0.0
            )
        return by_domain

    # ---------- اقتراح الاستراتيجية ----------
    def suggest_strategy(self, task_type: str, title: str) -> Dict[str, Any]:
        domain = self.infer_domain(task_type, title)
        profile = self.summarize_profile()
        dom_stats = profile.get(domain, {})
        success_rate = dom_stats.get("success_rate", 0.0)
        avg_score = dom_stats.get("avg_score", 0.0)
        strategy: Dict[str, Any] = {
            "domain": domain,
            "preferred_engines": [],
            "use_deep_cot": False,
            "use_rag": False,
            "cot_samples": 1,
            "risk_level": "normal",
        }
        # قواعد لكل دومين
        if domain.startswith("medical"):
            strategy["preferred_engines"] = ["hosted_llm", "retriever"]
            strategy["use_rag"] = True
            strategy["risk_level"] = "high"
            if avg_score < 0.8 or success_rate < 0.7:
                strategy["use_deep_cot"] = True
                strategy["cot_samples"] = 3
        elif domain.startswith("math"):
            strategy["preferred_engines"] = ["hosted_llm", "deliberation"]
            strategy["use_deep_cot"] = True
            strategy["cot_samples"] = 3
            strategy["risk_level"] = "high"
        elif domain.startswith("project"):
            strategy["preferred_engines"] = ["planner", "timeline", "motivation"]
            strategy["risk_level"] = "medium"
            strategy["use_deep_cot"] = False
            strategy["cot_samples"] = 1
        else:
            strategy["preferred_engines"] = ["hosted_llm"]
            if avg_score < 0.6:
                strategy["use_deep_cot"] = True
                strategy["cot_samples"] = 2
        # تعديل إضافي لو النجاح ضعيف جدًا عبر الزمن
        if success_rate < 0.5 and (
            profile.get(domain, {}).get("count", 0) >= 3
        ):
            strategy["use_deep_cot"] = True
            strategy["cot_samples"] = max(strategy["cot_samples"], 3)
            strategy["risk_level"] = "high"
        return strategy

    # ---------- تسجيل النتائج ----------
    def record_outcome(
        self,
        title: str,
        task_type: str,
        score: Optional[float],
        success: Optional[bool],
        meta: Optional[Dict[str, Any]] = None,
        strategy: Optional[Dict[str, Any]] = None,
    ) -> None:
        domain = self.infer_domain(task_type, title)
        item = MemoryItem(
            ts=time.time(),
            task_title=title or "",
            task_type=task_type or "unknown",
            domain=domain,
            strategy=strategy or {},
            score=score,
            success=bool(success) if success is not None else None,
            meta=meta or {},
        )
        try:
            self.append(item)
        except Exception:
            pass

    # ---------- واجهة مريحة ----------
    @classmethod
    def default(cls) -> "StrategicMemory":
        return cls(path=_default_path())
