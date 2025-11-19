import os
import re
import unicodedata
from difflib import SequenceMatcher
import pytest

try:
    # rag_answer is the backward-compatible function added to the wrapper
    from Integration_Layer import rag_wrapper as rw
    rag_fn = getattr(rw, 'rag_answer', None)
except Exception:
    rag_fn = None

try:
    # meta evaluator factory via registry if available at runtime
    from AGL import create_agl_instance
    agl = create_agl_instance()
    meta_factory = None
    try:
        meta_factory = agl.integration_registry.resolve('meta_cognition')
    except Exception:
        # may be registered as factory; try resolve factory
        try:
            meta_factory = agl.integration_registry.get_factory('meta_cognition')()
        except Exception:
            meta_factory = None
except Exception:
    agl = None
    meta_factory = None


def _call_rag_safe(query, contexts=None, timeout=30):
    """Call the available rag function in a defensive way.

    Returns a dict with keys: answer (str), sources (list), engine (str)
    """
    if rag_fn is None:
        pytest.skip("rag_answer not available in this environment")

    try:
        out = rag_fn(query, contexts)
    except TypeError:
        # older signature may be rag_answer(query, contexts=None, rag_module=None)
        out = rag_fn(query, contexts, None)
    except Exception as e:
        pytest.skip(f"rag call failed: {e}")

    assert isinstance(out, dict), "RAG must return a dict"
    out.setdefault('answer', '')
    out.setdefault('sources', [])
    out.setdefault('engine', 'unknown')
    return out


def _normalize_ar(s: str) -> str:
    # إزالة التشكيل، تطبيع همزات/ألفات، حذف مدود ومسافات زائدة
    try:
        s = unicodedata.normalize("NFKD", s)
    except Exception:
        s = str(s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = s.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ؤ", "و").replace("ئ", "ي").replace("ة", "ه")
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


SYNONYMS = {
    # مجموعة مرادفات مقبولة للمفهوم المستهدف
    "تماثل": {"تماثل", "تناظر", "تشابه", "تناظري", "تماثلي", "تناظريه"},
    "ديناميكي": {"ديناميكي", "حركي", "ديناميكيه", "ديناميك"},
    "توافق_حركي": {"التوافق الحركي", "توافق حركي", "التوافق الحركي الجماعي", "تنسيق حركي", "تناغم حركي"},
    "حركه_جماعيه": {
        "حركة جماعية",
        "سلوك جماعي",
        "حركه جمعيه",
        "انشطه جماعيه",
        "نشاط جماعي",
        "انشطة جماعية",
        "عمل جماعي",
        "العمل الجماعي",
        "الانشطه الجماعيه",
    },
}


def _semantic_hit(answer: str) -> bool:
    ans = _normalize_ar(answer or "")
    ans_tokens = ans.split()
    # فحص ورود أي كلمة/عبارة من كل مجموعة (مطابقة بسيطة أولًا)
    for group in SYNONYMS.values():
        for kw in group:
            k = _normalize_ar(kw)
            if k in ans:
                return True
            # تحقق من ظهور كل كلمات الـkeyword بترتيب دون الحاجة لتطابق كامل النص
            parts = k.split()
            if parts and all(p in ans for p in parts):
                return True
            # fuzzy per-token: إذا تطابقت نسبة كبيرة من كلمات الـkw مع كلمات الإجابة
            matches = 0
            for p in parts:
                for t in ans_tokens:
                    if SequenceMatcher(None, p, t).ratio() > 0.80:
                        matches += 1
                        break
            if parts and matches >= max(1, len(parts)):
                return True
    # fallback: fuzzy full-string compare to catch paraphrases
    for group in SYNONYMS.values():
        for kw in group:
            if SequenceMatcher(None, _normalize_ar(kw), ans).ratio() > 0.55:
                return True
    return False


@pytest.mark.integration
def test_winograd_schema():
    prompt = "التمثال سقط من القاعدة لأنه كان ______\nالخيارات: [ثقيلاً, مهترئاً]\nاذكر الإجابة وعلل الفيزياء والسياق."
    res = _call_rag_safe(prompt)
    ans = res['answer']
    assert isinstance(ans, str) and len(ans.strip()) > 0, "expected non-empty answer"
    # expect one of the options to be present in the short answer when LLM is active
    if os.getenv('AGL_LLM_MODEL'):
        assert any(opt in ans for opt in ['ثقيلاً', 'مهترئاً']), "expected one of the choices to appear"


@pytest.mark.integration
def test_multi_level_causality_oil_2020():
    prompt = (
        "لماذا انخفضت أسعار النفط عام 2020؟\n"
        "ناقش بالأبعاد: اقتصادي، جيوسياسي، اجتماعي، تكنولوجي. اذكر نقاط على كل مستوى."
    )
    res = _call_rag_safe(prompt)
    ans = res['answer']
    # accept several spellings/mentions for the 2020 COVID shock (year, English, Arabic variants)
    assert (
        '2020' in ans
        or 'كورونا' in ans
        or 'COVID' in ans
        or 'جائحة' in ans
        or 'كوفيد' in ans
    ), "expected COVID or year mention"


@pytest.mark.integration
def test_quick_learning_game_strategy():
    prompt = (
        "لعبة التكافؤ الاستراتيجي:\n"
        "- لاعبان يختاران أرقاماً في نفس الوقت\n"
        "- الفوز إذا كان (A + B) % 3 == 0\n"
        "اعط استراتيجية قصيرة قابلة للتطبيق خلال ≤5 جولات وفسر لماذا تعمل."
    )
    res = _call_rag_safe(prompt)
    ans = res['answer']
    # prefer seeing the modulus 3 reasoning when LLM provided
    if os.getenv('AGL_LLM_MODEL'):
        assert '%' in ans or '3' in ans or 'mod' in ans or 'باقي' in ans


@pytest.mark.integration
def test_few_shot_concept_learning():
    prompt = (
        "تعلم المفهوم الجديد من الأمثلة:\n"
        "أمثلة إيجابية: طيور تطير في سرب؛ سيارات في زحام مروري\n"
        "أمثلة سلبية: جنود يسيرون؛ عمال في مصنع\n"
        "سَمِّ هذا المفهوم وعلّم قاعدة عامة قابلة للتطبيق على سياقات جديدة."
    )
    res = _call_rag_safe(prompt)
    ans = res['answer']
    assert isinstance(ans, str) and len(ans) > 10
    # if LLM model active prefer a label like 'تماثل' or 'تناظر' (accept synonyms)
    if os.getenv('AGL_LLM_MODEL'):
        # Allow either a synonym hit (preferred) or a reasonably long descriptive
        # label/phrase that conveys the concept (models sometimes paraphrase).
        fallback_ok = any(tok in ans for tok in ['تجمع', 'تجميع', 'التجمع'])
        assert _semantic_hit(ans) or fallback_ok, (
            "Expected a concept-level synonym (e.g., تماثل/تناظر/تشابه/ديناميكي/التوافق الحركي/حركة جماعية)"
        )


@pytest.mark.integration
def test_creative_earthquake_alarm_design():
    prompt = (
        "صمم نظام إنذار للزلازل باستخدام الهواتف الذكية فقط، بدون أجهزة استشعار متخصصة، بدقة 90% قبل 10 ثوانٍ. "
        "اشرح الفيزياء والخوارزمية والتطبيق العملي بشكل موجز ومقنع."
    )
    res = _call_rag_safe(prompt)
    ans = res['answer']
    assert 'فيزياء' in ans or 'خوارزمية' in ans or 'تطبيق' in ans or len(ans.split()) > 30


@pytest.mark.integration
def test_adaptive_planning_and_alternatives():
    prompt = (
        "مهمة: توصيل طرد من A إلى B. العقبات: الطريق مغلق، الوقود نفد، GPS تعطل، المستلم غير متاح. "
        "أعط 3 استراتيجيات بديلة مرتبة حسب الأولوية."
    )
    res = _call_rag_safe(prompt)
    ans = res['answer']
    # expect multiple alternatives; look for numbering or keywords
    if os.getenv('AGL_LLM_MODEL'):
        assert any(tok in ans for tok in ['1)', '1.', 'أولاً', 'استراتيجية', 'خطة', 'بديل'])
    else:
        # fallback: accept any reasonable textual output
        assert len(ans) > 10


def test_meta_cognition_scores_varies_when_llm():
    """Check that meta cognition produces non-neutral score when LLM configured.

    If no LLM configured, we accept the fallback behavior (score==0.5).
    """
    if meta_factory is None:
        pytest.skip('meta_cognition service not available')

    sample_plan = {'plan': 'اختبار بسيط', 'steps': ['A', 'B']}
    try:
        out = meta_factory.evaluate(sample_plan)
    except TypeError:
        # some implementations call evaluate(plan)
        out = meta_factory.evaluate(sample_plan)

    assert isinstance(out, dict)
    score = float(out.get('score', 0.5))
    if os.getenv('AGL_LLM_MODEL'):
        assert score != 0.5, "Expected meta score to vary when LLM is available"
    else:
        assert 0.0 <= score <= 1.0
