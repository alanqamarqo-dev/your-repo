from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# مكان تخزين الملف الرئيسي للبروفايل
ROOT_DIR = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = ROOT_DIR / "artifacts"
PROFILE_PATH = ARTIFACTS_DIR / "self_profile.json"


def _ensure_artifacts_dir() -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


def _load_profile(path: Path = PROFILE_PATH) -> Dict[str, Any]:
    """
    تحميل بروفايل النظام من ملف JSON.
    لو الملف غير موجود يرجع قاموسًا فارغًا.
    """
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # في حالة تلف الملف، نبدأ من جديد
        return {}


def _save_profile(profile: Dict[str, Any], path: Path = PROFILE_PATH) -> None:
    """
    حفظ البروفايل إلى ملف JSON.
    """
    _ensure_artifacts_dir()
    with path.open("w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)


def _update_domain_stats(
    domain_stats: Dict[str, Any],
    score: float,
    engines: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    تحديث إحصائيات مجال معين (مثل "medical" أو "math") بناءً على نتيجة جديدة.
    """
    calls = int(domain_stats.get("calls", 0))
    avg = float(domain_stats.get("accuracy", 0.0))

    new_calls = calls + 1
    # تحديث المتوسط التراكمي
    new_avg = ((avg * calls) + score) / new_calls

    history = list(domain_stats.get("history", []))
    history.append(
        {
            "ts": time.time(),
            "score": score,
            "engines": engines or [],
        }
    )
    # لتفادي التضخم، نحتفظ بآخر 100 نقطة فقط
    if len(history) > 100:
        history = history[-100:]

    engines_used = set(domain_stats.get("engines", []))
    if engines:
        engines_used.update(engines)

    domain_stats.update(
        {
            "calls": new_calls,
            "accuracy": new_avg,
            "last_score": score,
            "engines": sorted(engines_used),
            "history": history,
        }
    )
    return domain_stats


def record_eval_result(
    domain: str,
    score: float,
    engines: Optional[List[str]] = None,
    meta: Optional[Dict[str, Any]] = None,
    path: Path = PROFILE_PATH,
) -> None:
    """
    تسجيل نتيجة تقييم جديدة في بروفايل الذات.
    domain: المجال (مثلاً "medical" أو "math" أو "planning").
    score: من 0 إلى 1.
    engines: قائمة المحركات المستخدمة في هذه المهمة.
    meta: معلومات إضافية اختيارية.
    """
    profile = _load_profile(path)
    domains = profile.setdefault("domains", {})

    domain_stats = domains.get(domain, {})
    domain_stats = _update_domain_stats(domain_stats, score, engines)
    domains[domain] = domain_stats

    # تخزين مستوى عام لو أحببنا
    profile["last_update_ts"] = time.time()
    if meta is not None:
        meta_hist = list(profile.get("meta_history", []))
        meta_hist.append(
            {
                "ts": time.time(),
                "domain": domain,
                "score": score,
                "meta": meta,
            }
        )
        if len(meta_hist) > 200:
            meta_hist = meta_hist[-200:]
        profile["meta_history"] = meta_hist

    profile["domains"] = domains
    _save_profile(profile, path)


def _infer_domain_from_problem(problem: Dict[str, Any]) -> str:
    """
    محاولة بسيطة لتخمين المجال من السؤال/العنوان.
    هذه نسخة خفيفة للاختبارات، يمكن تحسينها لاحقًا.
    """
    # لو فيه domain صريح استخدمه
    explicit = problem.get("domain")
    if isinstance(explicit, str) and explicit:
        return explicit

    text = (problem.get("title") or "") + " " + (problem.get("question") or "")
    text = text.strip()

    medical_keywords = ["ضغط الدم", "سكري", "الكلى", "الإنفلونزا", "دواء", "أعراض"]
    math_keywords = ["تكامل", "مصفوفة", "احتمال", "مشتقة", "معادلة"]
    planning_keywords = ["خطة", "مشروع", "مرحلة", "تنفيذ", "مهام"]

    if any(k in text for k in medical_keywords):
        return "medical"
    if any(k in text for k in math_keywords):
        return "math"
    if any(k in text for k in planning_keywords):
        return "planning"

    return "general"


def suggest_strategy(
    problem: Optional[Dict[str, Any]] = None,
    path: Path = PROFILE_PATH,
) -> Dict[str, Any]:
    """
    اقتراح استراتيجية تفكير/محركات بناءً على بروفايل الذات.
    ترجع قاموسًا مثل:
    {
      "domain": "...",
      "use_cot": True/False,
      "cot_samples": 1..5,
      "use_rag": True/False,
      "preferred_engines": [...]
    }
    """
    profile = _load_profile(path)
    domains = profile.get("domains", {})

    if problem is None:
        domain = "general"
    else:
        domain = _infer_domain_from_problem(problem)

    stats = domains.get(domain, {})
    acc = float(stats.get("accuracy", 0.0))
    engines = stats.get("engines", [])

    # سياسة بسيطة يمكن تطويرها لاحقًا
    if acc < 0.5:
        # أداء ضعيف → نستخدم CoT قوي + RAG
        strategy = {
            "domain": domain,
            "use_cot": True,
            "cot_samples": 3,
            "use_rag": True,
            "preferred_engines": engines or ["hosted_llm", "retriever"],
        }
    elif acc < 0.8:
        # أداء متوسط → CoT متوسط، RAG اختياري
        strategy = {
            "domain": domain,
            "use_cot": True,
            "cot_samples": 2,
            "use_rag": False,
            "preferred_engines": engines or ["hosted_llm"],
        }
    else:
        # أداء جيد → إجابة مباشرة أو CoT خفيف
        strategy = {
            "domain": domain,
            "use_cot": False,
            "cot_samples": 1,
            "use_rag": False,
            "preferred_engines": engines or ["hosted_llm"],
        }

    return strategy
