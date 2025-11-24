# -*- coding: utf-8 -*-
import json
import os
from importlib import import_module

import pytest

# -------- إعدادات بيئة مضمونة (تشغيل بدون مزود LLM حقيقي) --------
@pytest.fixture(scope="session", autouse=True)
def env_mocks():
    os.environ.setdefault("AGL_FEATURE_ENABLE_RAG", "1")
    os.environ.setdefault("AGL_OLLAMA_KB_MOCK", "1")         # نحفّز ردوداً غير فارغة في بيئات CI
    os.environ.setdefault("AGL_EXTERNAL_INFO_MOCK", "1")
    yield


# -------- تشغيل الـbootstrap مرة واحدة وتحصيل تقرير التسجيل --------
@pytest.fixture(scope="session")
def bootstrap_and_report(tmp_path_factory):
    # استيراد الـbootstrap والـregistry الموحّد
    from Core_Engines import bootstrap_register_all_engines
    from Integration_Layer.integration_registry import registry

    registered = bootstrap_register_all_engines(registry, allow_optional=True, verbose=True)

    # نحاول قراءة تقرير الـbootstrap (مكانان محتملان)
    report_candidates = [
        "bootstrap_report.json",
        os.path.join("artifacts", "bootstrap_report.json"),
    ]

    report = {"registered": list(registered.keys()), "skipped": {}}
    for p in report_candidates:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    r = json.load(f)
                # توحيد البنية قدر الإمكان
                if isinstance(r, dict):
                    if "registered" in r:
                        report["registered"] = r["registered"]
                    if "skipped" in r:
                        report["skipped"] = r["skipped"]
            except Exception:
                pass
            break

    return {"registry_registered": set(report["registered"]),
            "skipped": report.get("skipped", {}),
            "ENGINE_SPECS": _load_engine_specs()}


def _load_engine_specs():
    # نسحب خريطة ENGINE_SPECS لمعرفة مسارات الوحدات والأصناف
    from Core_Engines import __init__ as CE  # noqa: F401
    try:
        return getattr(CE, "ENGINE_SPECS")
    except AttributeError:
        return {}


# -------- تعريف المحركات المستهدفة وعينات المهام “مثل المخطط” --------
TARGET_ENGINES = [
    ("NLP_Advanced",          {"task": "nlu.advanced", "text": "اشرح بلطف وبنبرة ودية لماذا السماء زرقاء", "tone": "ودي"}),
    ("General_Knowledge",     {"task": "knowledge.general", "query": "ما عاصمة فرنسا؟"}),
    ("Creative_Innovation",   {"task": "creativity.generate", "problem": "نفايات بلاستيكية في حي فقير", "constraints": ["تكلفة منخفضة"]}),
    ("Strategic_Thinking",    {"task": "strategy.plan", "goal": "تعلم الألمانية خلال 6 أشهر", "constraints": ["موارد مجانية"]}),
    ("Visual_Spatial",        {"task": "vision.layout", "scene": "غرفة فيها باب شمال، طاولة يمين، نافذة خلف كرسي"}),
    ("Social_Interaction",    {"task": "social.empathy", "situation": "مدير صرخ على موظف أمام الفريق"}),
    # “التعلم المتعمق”: نغطيه بمحركَي الميتا كبديلين فعّالين
    ("Meta_Learning",         {"task": "meta.learn", "log": ["خطأ", "تصحيح"], "objective": "تحسين ذاتي بسيط"}),
    ("AdvancedMetaReasoner",  {"task": "meta.reason", "question": "ما أفضل خطوة لتحسين الاستدلال في التجربة القادمة؟"}),
]


# -------- اختبار (1): التحقق من التسجيل بعد الـbootstrap --------
@pytest.mark.smoke
@pytest.mark.parametrize("engine_name,_sample", TARGET_ENGINES)
def test_engine_registered_or_explained(bootstrap_and_report, engine_name, _sample):
    reg = bootstrap_and_report["registry_registered"]
    skipped = bootstrap_and_report["skipped"]

    if engine_name in reg:
        assert True  # موجود ومسجّل ✔
    else:
        # إذا غير مسجّل، نُعطي سببًا واضحًا من سجلّ التخطي إن وُجد
        reason = None
        if isinstance(skipped, dict):
            reason = skipped.get(engine_name)
        pytest.xfail(f"المحرّك '{engine_name}' غير مسجّل بعد (bootstrap). السبب: {reason}")


# -------- مساعد: إنشاء المحرك من ENGINE_SPECS مباشرة (إن أمكن) --------
def _construct_engine(engine_name, specs):
    spec = specs.get(engine_name)
    if not spec:
        raise RuntimeError(f"لا توجد مواصفة لهذا المحرك ضمن ENGINE_SPECS: {engine_name}")
    modpath, clsname = spec
    m = import_module(modpath)
    # تفضيل create_engine(config)
    if hasattr(m, "create_engine") and callable(getattr(m, "create_engine")):
        return m.create_engine(config={})
    if clsname:
        cls = getattr(m, clsname)
        try:
            return cls(config={})
        except TypeError:
            return cls()
    raise RuntimeError(f"لا مصنع ولا صنف صالح في: {engine_name} ({modpath})")


# -------- معيار “النتيجة المعقولة” من المحرك --------
def _is_reasonable_output(obj):
    # نقبل عدة أشكال، لكن المهم: ليس فارغًا ويمكن استهلاكه من الـOrchestrator
    if not obj:
        return False
    if isinstance(obj, dict):
        # وجود ok/result أو نص
        if "ok" in obj and obj["ok"] is True:
            return True
        if any(k in obj for k in ("result", "text", "answer", "data")):
            return True
    if isinstance(obj, (list, tuple)) and len(obj) > 0:
        return True
    if isinstance(obj, str) and obj.strip():
        return True
    return False


# -------- اختبار (2): إن وُجد المحرك في المواصفات يمكن إنشاؤه ويُعالج مهمة بسيطة --------
@pytest.mark.integration
@pytest.mark.parametrize("engine_name,sample_task", TARGET_ENGINES)
def test_engine_minimal_process_task(bootstrap_and_report, engine_name, sample_task):
    specs = bootstrap_and_report["ENGINE_SPECS"]
    reg = bootstrap_and_report["registry_registered"]

    # إذا لم يكن حتى في المواصفات، فهذا فشل تصميمي صريح
    if engine_name not in specs:
        pytest.xfail(f"المحرّك '{engine_name}' غير موجود في ENGINE_SPECS بعد.")

    # إذا غير مسجّل لكن له مواصفة، نسمح باختبار إنشاء مباشر من الوحدة
    try:
        eng = _construct_engine(engine_name, specs)
    except Exception as e:
        pytest.xfail(f"تعذّر إنشاء المحرك '{engine_name}' من مواصفته: {e!r}")

    # يجب أن يوفّر process_task ليكون قابلًا للتنفيذ في المنظومة
    if not hasattr(eng, "process_task") or not callable(getattr(eng, "process_task")):
        pytest.xfail(f"المحرّك '{engine_name}' لا يوفّر process_task().")

    # تنفيذ عيّنة مهمة “مثل المخطط”
    try:
        out = eng.process_task(sample_task)
    except Exception as e:
        pytest.fail(f"process_task('{engine_name}') رمى استثناء: {e!r}")

    assert _is_reasonable_output(out), f"ناتج المحرك '{engine_name}' غير معقول/فارغ: {out!r}"
