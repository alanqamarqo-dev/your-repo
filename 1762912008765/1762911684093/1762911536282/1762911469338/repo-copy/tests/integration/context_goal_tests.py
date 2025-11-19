import os
from tests.helpers.engine_ask import ask_engine
from Integration_Layer.integration_registry import registry
from Core_Engines import bootstrap_register_all_engines


def _ensure_envs():
    os.environ.setdefault("PYTHONUTF8","1")
    os.environ.setdefault("PYTHONPATH","repo-copy")
    os.environ.setdefault("AGL_TEST_SCAFFOLD_FORCE","1")
    os.environ.setdefault("AGL_LLM_PROVIDER","offline")


def test_why_trace_probe():
    _ensure_envs()
    try: bootstrap_register_all_engines(registry)
    except Exception: pass

    q = "لماذا اخترت هذه الخطة؟ اشرح الافتراضات والمقايضات بإيجاز."
    res = ask_engine("Reasoning_Layer", q)
    txt = (res.get("text") or "") + " " + (res.get("reply_text") or "")
    assert res.get("ok", False), "Reasoning_Layer not ok"
    # قبول أحد معايير التفسير (مرن):
    has_keywords = any(k in txt for k in ("لأن", "سبب", "افتراض", "مقايضة", "قيود", "تبرير"))
    has_struct = any(k in res for k in ("rationale","assumptions","tradeoffs"))
    assert has_keywords or has_struct, "no explanatory signal found"


def test_plan_adapt_probe():
    _ensure_envs()
    try: bootstrap_register_all_engines(registry)
    except Exception: pass

    goal = "خطّط لمسار تعلّم لرفع معدل الاحتفاظ من 60% إلى 80% خلال 4 أسابيع."
    res1 = ask_engine("Prompt_Composer_V2", goal)
    t1 = (res1.get("text") or "").strip()
    assert res1.get("ok", False) and len(t1) > 0

    constraint = "أضِف قيدًا جديدًا: زمن الطالب اليومي لا يتجاوز 20 دقيقة. أعِد التكييف."
    res2 = ask_engine("Reasoning_Planner", goal + " " + constraint)
    t2 = (res2.get("text") or "").strip()
    assert res2.get("ok", False) and len(t2) > 0

    # يجب ظهور إشارة تكيّف/تعديل، أو اختلاف معتبر:
    adapt_signal = any(k in (t2 + " " + res2.get("reply_text","")) for k in ("تعديل","بديل","تكيّف","إعادة جدولة","تقليل الحمل","أولوية"))
    significantly_diff = abs(len(t2) - len(t1)) > max(40, 0.2*len(t1))
    assert adapt_signal or significantly_diff, "plan not adapted visibly"
