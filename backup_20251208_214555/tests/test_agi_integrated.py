import os
import sys
import json
from pathlib import Path

# ensure repo root on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from Integration_Layer.Conversation_Manager import start_session, auto_route_and_respond


ARTIFACTS = Path(ROOT) / 'artifacts'
ARTIFACTS.mkdir(exist_ok=True)


PROMPTS = {
    'part1': (
        "صمم خطة لإنقاذ قرية معزولة تواجه مجاعة بسبب الجفاف، مع الأخذ في الاعتبار: "
        "القيود الاقتصادية (ميزانية ١٠٠٠ دولار فقط)، العوامل البيئية المحلية، الحلول التكنولوجية البسيطة، "
        "الجوانب النفسية والاجتماعية للسكان، واستدامة الحل بعد عامين"
    ),
    'part2': (
        "تعلم هذه القواعد الجديدة للعبة خلال دقيقتين ثم اشرح كيف ستفوز: "
        "اللعبة تتضمن ٣ لاعبين وألواح ملونة. كل لاعب يختار لونًا مختلفًا كل جولة. "
        "النقاط تحسب بناءً على ترتيب الألوان. هناك قواعد خاصة عندما يتطابق لونان."
    ),
    'part3': (
        "اخترع جهازًا باستخدام مواد معاد تدويرها فقط (زجاجات بلاستيك، أوراق، خيوط) لحل مشكلة تواجه سكان المناطق الحضرية الفقيرة. "
        "صف كيف يعمل ولماذا هذا الحل مبتكر وفعال."
    ),
    'part4': (
        "في هذا الموقف: مدير يصرخ على موظف أمام زملائه لأن مشروعًا تأخر. "
        "حلل المشاعر المختلفة لكل شخص حاضر، واقترح حلاً يصلح العلاقات مع الحفاظ على الإنتاجية."
    ),
    'part5': (
        "ارسم خطة لتعلم لغة جديدة في ٦ أشهر، مع تحديد: الموارد المجانية المتاحة، طريقة قياس التقدم، "
        "التحديات المتوقعة وكيفية التغلب عليها، وكيف ستتحدث مع متحدث أصلي بعد ٣ أشهر فقط."
    ),
}


def simple_keyword_checks(text: str, keywords: list) -> float:
    """Return fraction of keywords present in text (case-insensitive)."""
    if not text:
        return 0.0
    t = text.lower()
    found = sum(1 for k in keywords if k.lower() in t)
    return found / max(1, len(keywords))


def test_agi_integrated_run_and_record():
    """Run the 5-part AGI integrated prompts through the local pipeline and save results.

    The test asserts that the pipeline produced a textual response for each part and
    writes `artifacts/agi_test_results.json` containing raw responses and lightweight scores.
    """
    sid = f'test_agi_{os.getpid()}'
    start_session(sid)

    results = {}

    keyword_expect = {
        'part1': ['ميزانية', 'مياه', 'استدامة', 'تقنية', 'مجتمع', 'عامين'],
        'part2': ['قواعد', 'لاعب', 'نقاط', 'جولة', 'يتطابق', 'استراتيجية'],
        'part3': ['زجاج', 'بلاستيك', 'خيوط', 'معاد تدويرها', 'جهاز', 'يعمل'],
        'part4': ['غضب', 'احراج', 'مدير', 'موظف', 'اعتذار', 'حل'],
        'part5': ['شهر', 'موارد', 'قياس', 'تحدي', 'متحدث', '٦'],
    }

    for pid, prompt in PROMPTS.items():
        try:
            resp = auto_route_and_respond(sid, prompt)
        except Exception as e:
            resp = {'ok': False, 'error': 'exception', 'detail': str(e)}

        # prefer common fields
        if isinstance(resp, dict):
            text = resp.get('reply_text') or resp.get('text') or resp.get('output') or ''
            if isinstance(text, dict):
                text = text.get('reply') or text.get('text') or ''
            if text is None:
                text = ''
            text = str(text)
        else:
            text = str(resp)

        score = simple_keyword_checks(text, keyword_expect.get(pid, []))
        results[pid] = {
            'prompt': prompt,
            'response': text,
            'ok': isinstance(resp, dict) and resp.get('ok', True),
            'keyword_score': score,
            'raw': resp,
        }

    out_path = ARTIFACTS / 'agi_test_results.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # Basic assertions: we expect a non-empty response string for each part
    for pid, entry in results.items():
        assert isinstance(entry['response'], str), f"{pid} response must be a string"
        # ensure pipeline returned something; allow short answers but not empty
        assert entry['response'].strip() != '', f"{pid} produced empty response"

    # Test passes if every part produced a response; deeper scoring is saved to artifacts
