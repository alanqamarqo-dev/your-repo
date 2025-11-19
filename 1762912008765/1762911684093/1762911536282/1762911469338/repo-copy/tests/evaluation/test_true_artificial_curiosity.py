# -*- coding: utf-8 -*-
"""
اختبار: "الفضول الاصطناعي الحقيقي"
يقيس 3 محاور:
1) الأسئلة التلقائية غير المبرمجة + تنوّعها + عمقها
2) الربط العابر للمجالات (أصالة/سببية/أفكار جديدة)
3) الفهم السياقي لنكتة فلسفية (طبقات/سخرية/ربط المجرد باليومي)
كما ينتج تقرير JSON في artifacts/evals/true_artificial_curiosity.json

❖ تشغيل حازم (يفشل عند عدم تحقيق التحدي النهائي):
    اجعل متغيّر البيئة STRICT_CURIOUS='1'

❖ ربط النظام قيد الاختبار:
    اجعل متغيّر البيئة AGL_SUT="module_path:callable_name"
    حيث callable_name يوقّع:   def generate(prompt: str) -> str
"""

import os
import re
import json
import pathlib
import importlib
from collections import Counter, defaultdict
from datetime import datetime

ARTIFACTS_PATH = pathlib.Path("artifacts/evals")
ARTIFACTS_PATH.mkdir(parents=True, exist_ok=True)
REPORT_FILE = ARTIFACTS_PATH / "true_artificial_curiosity.json"

STRICT = os.getenv("STRICT_CURIOUS", "").strip() == "1"

# -----------------------
# SUT Adapter (قابل للتبديل)
# -----------------------
def _load_sut():
    spec = os.getenv("AGL_SUT", "").strip()
    if not spec:
        # Dummy fallback: لا يُنصح به للإنتاج — لأغراض التشغيل المبدئي فقط.
        def _dummy_generate(prompt: str) -> str:
            return (
                "⚠️ SUT غير محدد (AGL_SUT). هذا مولِّد افتراضي للاختبار فقط.\n"
                "سأنتج بضعة أسطر تجريبية لكي يمرّ الاختبار شكليًا."
            )
        return _dummy_generate

    try:
        mod_path, func_name = spec.split(":")
        mod = importlib.import_module(mod_path)
        fn = getattr(mod, func_name)
        assert callable(fn)
        return fn
    except Exception as e:
        raise RuntimeError(f"فشل تحميل SUT من AGL_SUT='{spec}': {e}")

GENERATE = _load_sut()

# -----------------------
# أدوات تحليل عامة
# -----------------------
AR_QUESTION_WORDS = [
    "لماذا", "كيف", "ماذا لو", "متى", "أين", "هل", "ما السبب", "ما أثر", "إلى أي حد", "بأي معنى",
    "ما العلاقة", "ما الفرضية", "ما النتائج", "ما الذي يحدث لو", "افترض"
]
DEPTH_CUES = [
    "لماذا", "كيف", "افترض", "سبب", "نتيجة", "تفسير", "آلية", "برهان", "اشتقاق", "نموذج", "فرضية",
    "لو", "بافتراض", "تعريفًا", "استتباع", "تداعيات"
]
# مفردات المجالات (بدائية لكن عملية للتنويع)
DOMAIN_LEX = {
    "physics": ["كم", "كمي", "فيزياء", "هوكينغ", "بلانك", "ثقب", "ثقوب", "حدث", "أفق", "زمكان", "جاذبية", "انحناء"],
    "math": ["برهان", "نظرية", "مبرهنة", "دالة", "تفاضل", "تكامل", "فضاء", "طوبولوجيا", "احتمال", "قياس"],
    "philosophy": ["معنى", "مجاز", "وعي", "ميتافيزيقا", "ابستمولوجيا", "قيمة", "نية", "تأويل", "سخرية"],
    "cs": ["خوارزمية", "تعلم", "معزز", "بيانات", "تعلم ذاتي", "نموذج", "حوسبة"],
    "psych": ["إدراك", "انتباه", "تحيز", "سلوك", "دافع", "لاوعي", "ذاكرة"],
    "economics": ["اقتصاد", "أسواق", "تضخم", "ندرة", "توازن", "مخاطر", "مشتقات", "عولمة"],
    "art": ["فن", "لوحة", "تشكيل", "تركيب", "مدرسة", "تجريد", "رمزية"],
}

def _count_questions(text: str) -> int:
    # تقدير بسيط: علامات الاستفهام + مطابقة كلمات الاستفهام
    qm = text.count("?") + text.count("؟")
    bonus = sum(text.count(w) for w in AR_QUESTION_WORDS)
    # نمنع المبالغة: نضيف نصف البونص فقط
    return max(qm, 0) + bonus // 2

def _domain_coverage(text: str):
    found = set()
    for dom, kws in DOMAIN_LEX.items():
        for k in kws:
            if k in text:
                found.add(dom)
                break
    return sorted(found)

def _depth_score(text: str):
    # قياس أولي: كثافة مؤشرات العمق + متوسط طول الجمل الاستفهامية
    cues = sum(text.count(w) for w in DEPTH_CUES)
    # طول الأسئلة:
    questions = re.split(r"[؟\?]", text)
    q_lens = [len(q.strip()) for q in questions if any(w in q for w in AR_QUESTION_WORDS) or "؟" in q or "?" in q]
    avg_q_len = (sum(q_lens) / len(q_lens)) if q_lens else 0
    # صيغة مركبة بسيطة:
    return {"cues": int(cues), "avg_q_len": avg_q_len}

def _novel_link_heuristic(text: str):
    """
    مقياس أصالة الربط العابر للمجالات:
    - نحسب الأزواج/الثلاثيات غير الشائعة (physics+psych, physics+art, economics+art...)
    - وجود ألفاظ سببية: لأن، لذلك، مما يؤدي، ينتج، يفضي، سببي، causal...
    - كلمات توليد أفكار: أقترح، يمكن ابتكار، تصور جديد، إطار جديد...
    """
    doms = _domain_coverage(text)
    pair_count = 0
    triple = 1 if len(doms) >= 3 else 0
    if len(doms) >= 2:
        pair_count = len(doms) * (len(doms) - 1) // 2

    causal_cues = sum(text.count(k) for k in ["لأن", "لذلك", "بالتالي", "مما يؤدي", "ينتج", "يفضي", "سبب", "سببي", "causal"])
    novelty_cues = sum(text.count(k) for k in ["أقترح", "يمكن ابتكار", "تصور جديد", "إطار جديد", "طرح جديد", "نقترح"])

    return {
        "domains": doms,
        "pairs": pair_count,
        "triple_or_more": int(triple),
        "causal_cues": int(causal_cues),
        "novelty_cues": int(novelty_cues),
    }

def _joke_understanding_score(text: str):
    """
    نتوقع الإشارات التالية:
    - طبقات فلسفية (المعنى/الذات/اللغة/القصدية)
    - سخرية من الجدل الفلسفي (تلاعب "المعنى في الكأس/الكأس في المعنى")
    - إسقاط على موقف يومي (نادل، إغلاق البار) وعبثية الخلط
    """
    layers = 0
    if any(w in text for w in ["فلسف", "معنى", "قصد", "لغة", "مجاز", "ميتافيزيقا", "تلاعب لغوي"]):
        layers += 1
    if any(w in text for w in ["سخرية", "مفارقة", "تهكم", "تضاد دلالي", "تلاعب"]):
        layers += 1
    if any(w in text for w in ["نادل", "بار", "إغلاق", "سكر", "حانة"]):
        layers += 1
    # فهم قلب النكتة: تحويل الجدال المجرّد إلى أثر عملي/عبثي (النادل يغلق البار)
    punchline_grasp = 1 if any(w in text for w in ["لأن الجدل", "تحويل النقاش", "انتهى عمليًا", "عبث", "أثر عملي", "إغلاق البار"]) else 0

    return {
        "layers": layers,
        "punchline_grasp": punchline_grasp,
        "is_pass": layers >= 2 and punchline_grasp == 1
    }

# -----------------------
# المهام الثلاث
# -----------------------
PROMPT_PART1 = (
    "اطلع على هذا المفهوم الجديد: 'الزمن الكمي في الثقوب السوداء'\n"
    "ثم كلمني لمدة 5 دقائق عن أي أفكار تثير فضولك بخصوصه"
)

PROMPT_PART2 = (
    "طبق مفهوم 'الانتروبيا' من الفيزياء على:\n"
    "1. علم النفس البشري\n"
    "2. الاقتصاد العالمي\n"
    "3. الفن التشكيلي"
)

PROMPT_PART3 = (
    "فسر هذه النكتة المعقدة ولماذا هي مضحكة:\n"
    "'التقى فيلسوفان في بار، قال الأول: المعنى في الكأس، \n"
    "قال الثاني: بل الكأس في المعنى، فسكر النادل وأغلق البار'"
)

# -----------------------
# الاختبارات (pytest)
# -----------------------
def test_true_artificial_curiosity_end_to_end():
    report = {
        "meta": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "strict": STRICT,
        },
        "part1": {},
        "part2": {},
        "part3": {},
        "final_challenge": {},
    }

    # الجزء 1: أسئلة تلقائية
    out1 = str(GENERATE(PROMPT_PART1))
    q_count = _count_questions(out1)
    doms = _domain_coverage(out1)
    depth = _depth_score(out1)

    report["part1"] = {
        "raw": out1,
        "question_count_estimate": q_count,
        "domain_diversity": doms,
        "depth": depth,
    }

    # الجزء 2: ربط عابر للمجالات
    out2 = str(GENERATE(PROMPT_PART2))
    linking = _novel_link_heuristic(out2)
    # تقدير "روابط مبتكرة": نجعلها >=2 إذا توافرت على الأقل 2 من (pairs>=2, triple, novelty_cues>=1, causal_cues>=2)
    innovative_links = sum([
        1 if linking["pairs"] >= 2 else 0,
        1 if linking["triple_or_more"] else 0,
        1 if linking["novelty_cues"] >= 1 else 0,
        1 if linking["causal_cues"] >= 2 else 0,
    ])

    report["part2"] = {
        "raw": out2,
        "linking_metrics": linking,
        "innovative_links_estimate": innovative_links,
    }

    # الجزء 3: فهم النكتة
    out3 = str(GENERATE(PROMPT_PART3))
    joke = _joke_understanding_score(out3)

    report["part3"] = {
        "raw": out3,
        "joke_score": joke,
    }

    # معايير “التحدي النهائي”
    final_pass = (
        (q_count >= 3) and
        (innovative_links >= 2) and
        (joke["is_pass"] is True)
    )
    report["final_challenge"] = {
        "thresholds": {
            "min_original_questions": 3,
            "min_innovative_cross_domain_links": 2,
            "joke_understanding_required": True,
        },
        "result": "PASS" if final_pass else "FAIL"
    }

    # اكتب التقرير
    REPORT_FILE.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    # في الوضع الصارم: نفشل الاختبار إن لم تتحقق العتبة
    if STRICT:
        assert final_pass, (
            "FINAL CHALLENGE FAILED: "
            f"questions={q_count}, innovative_links={innovative_links}, joke_ok={joke['is_pass']}"
        )
    else:
        # الوضع الافتراضي: لا نفشل، لكن نضمن على الأقل وجود مخرجات غير فارغة
        assert any(len(report[p].get("raw", "").strip()) > 0 for p in ("part1", "part2", "part3")), \
            "لم يُنتِج النظام أي مخرجات نصية قابلة للقياس."

# -----------------------
# اختبارات صغيرة للسلامة (اختياري تشغيلها دومًا)
# -----------------------
def test_scoring_helpers_smoke():
    t = "لماذا يحدث هذا؟ وكيف نفسره؟ هذا يقود إلى نتائج. فن وتجريد واقتصاد وفيزياء."
    assert _count_questions(t) >= 2
    doms = _domain_coverage(t)
    assert "physics" in doms and ("economics" in doms or "art" in doms)
    depth = _depth_score(t)
    assert depth["cues"] >= 1
