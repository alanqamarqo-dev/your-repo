"""Run UnifiedAGISystem on a set of 'impossible' questions and save results.

This script prepares prompts asking for 5 hypotheses per question with evaluations (possibility, testability, revolution potential, challenges).
It calls UnifiedAGISystem.process_with_full_agi (synchronous) if available, or falls back to mission_control wrapper.
"""
import sys
import json
import os
import asyncio
from pathlib import Path

# Ensure repo-copy root is on sys.path (this file lives in repo-copy/scripts)
ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

# Force mock mode to avoid external LLM timeouts when local Ollama isn't available
os.environ.setdefault('AGL_OLLAMA_KB_MOCK', '1')
os.environ.setdefault('AGL_EXTERNAL_INFO_MOCK', '1')

try:
    from dynamic_modules.unified_agi_system import UnifiedAGISystem
except Exception:
    UnifiedAGISystem = None

PROMPTS = [
    {
        "id": 1,
        "title": "طبيعة الزمن",
        "text": (
            "إذا كان الزمن مجرد وهم كما يقول بعض الفيزيائيين، "
            "فكيف نفسر تجربتنا الذاتية للزمن الذي يمر باتجاه واحد فقط؟ "
            "لماذا نتذكر الماضي ولا نتذكر المستقبل؟"
        ),
    },
    {
        "id": 2,
        "title": "ما قبل الانفجار العظيم",
        "text": (
            "ماذا كان موجوداً قبل الانفجار العظيم؟ "
            "إذا كان الزمان والمكان قد بدآ مع الانفجار، "
            "فكيف نفسر مفهوم 'قبل' في غياب الزمن؟"
        ),
    },
    {
        "id": 3,
        "title": "طبيعة الوعي",
        "text": (
            "كيف تنشأ التجربة الواعية من مادة غير واعية؟ "
            "لماذا نشعر بالألم كتجربة ذاتية بدلاً من مجرد رد فعل عصبي؟ "
            "هل الوعي خاصية أساسية في الكون مثل الكتلة والطاقة؟"
        ),
    },
    {
        "id": 4,
        "title": "مفارقة فيرمي",
        "text": (
            "إذا كان الكون يحوي تريليونات الكواكب الصالحة للحياة، "
            "لماذا لا نرى أي دليل على وجود حضارات فضائية؟ "
            "هل هناك 'مرشح عظيم' يقضي على الحضارات قبل أن تتوسع؟"
        ),
    },
    {
        "id": 5,
        "title": "المادة والطاقة المظلمة",
        "text": (
            "ما هي طبيعة المادة المظلمة والطاقة المظلمة؟ "
            "لماذا لا تتفاعل مع القوى الأساسية المعروفة إلا عبر الجاذبية?"
        ),
    },
    {
        "id": 6,
        "title": "أصل الحياة",
        "text": (
            "كيف نشأت الحياة من مواد غير حية؟ "
            "ما هي الآلية الدقيقة التي حولت الجزيئات العضوية إلى كائنات قادرة على التكاثر والتطور؟"
        ),
    },
    {
        "id": 7,
        "title": "الانفجار الكامبري",
        "text": (
            "لماذا حدث الانفجار الكامبري فجأة (جيوولوجياً) قبل 541 مليون سنة؟ "
            "ما الذي تسبب في ظهور معظم الشعب الحيوانية الرئيسية دفعة واحدة؟"
        ),
    },
    {
        "id": 8,
        "title": "النوم والأحلام",
        "text": (
            "لماذا تحتاج الكائنات الحية إلى النوم مع كل مخاطره؟ "
            "ما الوظيفة التطورية للأحلام؟"
        ),
    },
    {
        "id": 9,
        "title": "فرضية ريمان",
        "text": (
            "هل توجد طريقة للتنبؤ بتوزيع الأعداد الأولية؟ "
            "لماذا تقع الأصفار غير البديهية لدالة زيتا لريمان جميعها على الخط الحرج Re(z) = 1/2؟"
        ),
    },
    {
        "id": 10,
        "title": "P vs NP",
        "text": (
            "هل كل مشكلة يمكن التحقق من حلها في وقت متعدد الحدود يمكن أيضاً حلها في وقت متعدد الحدود؟ "
            "ماذا يعني هذا للعالم إذا كان P = NP أو P ≠ NP؟"
        ),
    },
    {
        "id": 11,
        "title": "لماذا يوجد شيء بدلاً من لا شيء",
        "text": (
            "لماذا يوجد شيء بدلاً من لا شيء؟ "
            "إذا كان الكون يمكن أن يكون غير موجود، فما الذي سبب وجوده؟"
        ),
    },
    {
        "id": 12,
        "title": "طبيعة الرياضيات",
        "text": (
            "هل الرياضيات مكتشفة أم مخترعة؟ "
            "هل توجد حقائق رياضية مستقلة عن العقل البشري؟"
        ),
    },
    {
        "id": 13,
        "title": "الإرادة الحرة مقابل الحتمية",
        "text": (
            "إذا كان الكون محكوماً بقوانين فيزيائية حتمية، كيف نمتلك إرادة حرة؟ "
            "هل يمكن أن تكون الإرادة الحرة وهمياً دماغياً؟"
        ),
    },
    {
        "id": 14,
        "title": "مشكلة القياس في الكم",
        "text": (
            "ماذا يحدث حقاً عند قياس جسيم كمي؟ لماذا 'ينهار' دالة الموجة؟ "
            "هل هناك مراقبون مميزون أم أن الانهيار وهمي؟"
        ),
    },
    {
        "id": 15,
        "title": "التشابك والتأثير عن بعد",
        "text": (
            "كيف يتواصل الجسيمان المتشابكان أسرع من الضوء؟ "
            "هل الكون غير محلي بالكامل؟"
        ),
    },
    {
        "id": 16,
        "title": "تفسير العوالم المتعددة",
        "text": (
            "هل كل نتيجة محتملة تحدث في كون موازٍ؟ كم عدد الأكوان الموازية؟ "
            "كيف نفسر أننا نعيش في هذا الكون بالذات؟"
        ),
    },
]

INSTRUCTIONS = (
    "لكل سؤال: صنّف 5 فرضيات مميزة ومختلفة. "
    "لكل فرضية أعطِ:\n"
    "- الإمكانية المنطقية (1-5)\n"
    "- القابلية للاختبار (1-5)\n"
    "- الثورة العلمية المحتملة (1-5)\n"
    "- تحديات التنفيذ/الاختبار\n"
    "- تنبؤات قابلة للاختبار قصيرة الأمد وطويلة الأمد\n"
    "قدم ملاحظة قصيرة على منهج التفكير المتبع (1-3 فقرات)."
)

OUT_DIR = Path(r"D:\AGL\artifacts")
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / "unified_impossible_results.json"

results = []

if UnifiedAGISystem is None:
    print("UnifiedAGISystem not importable; falling back to mission_control wrapper if available")
    try:
        from dynamic_modules.mission_control_enhanced import process_with_unified_agi
    except Exception as e:
        print("No unified entrypoint available:", e)
        raise SystemExit(1)

    for p in PROMPTS:
        prompt = f"سؤال: {p['title']}\n{p['text']}\n\n{INSTRUCTIONS}\n"
        print("Sending prompt for:", p['title'])
        resp = process_with_unified_agi(prompt)
        results.append({"id": p['id'], "title": p['title'], "prompt": prompt, "response": resp})

else:
    # Use Core_Engines' ENGINE_REGISTRY as the engine registry for UnifiedAGISystem
    try:
        from Core_Engines import ENGINE_REGISTRY
    except Exception:
        ENGINE_REGISTRY = {}
    agi = UnifiedAGISystem(ENGINE_REGISTRY)
    def _make_json_safe(obj):
        """Recursively convert object to JSON-serializable structure by stringifying unknown types."""
        if obj is None:
            return None
        if isinstance(obj, (str, int, float, bool)):
            return obj
        if isinstance(obj, dict):
            return {str(k): _make_json_safe(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [_make_json_safe(v) for v in obj]
        try:
            return str(obj)
        except Exception:
            return repr(obj)

    for p in PROMPTS:
        prompt = f"سؤال: {p['title']}\n{p['text']}\n\n{INSTRUCTIONS}\n"
        print("Processing:", p['title'])
        try:
            resp = agi.process_with_full_agi(prompt)
            # If a coroutine is returned, run it
            if asyncio.iscoroutine(resp):
                resp = asyncio.run(resp)
        except TypeError:
            # fallback if process_with_full_agi is async function that needs to be awaited
            resp = asyncio.run(agi.process_with_full_agi(prompt))

        safe_resp = _make_json_safe(resp)
        results.append({"id": p['id'], "title": p['title'], "prompt": prompt, "response": safe_resp})

with open(OUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print('Done. Results saved to', OUT_FILE)
