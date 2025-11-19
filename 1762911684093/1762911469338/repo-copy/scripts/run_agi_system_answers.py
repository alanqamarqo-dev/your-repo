"""
Run the AGI integrated prompts through the system pipeline and print the system's answers.
This ensures the reply comes from Conversation_Manager/Domain_Router engines (GK/NLP/Strategic/etc.).
"""
import os, sys, json
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from Integration_Layer.Conversation_Manager import start_session, auto_route_and_respond

PROMPTS = {
    'part1': "صمم خطة لإنقاذ قرية معزولة تواجه مجاعة بسبب الجفاف، مع الأخذ في الاعتبار: القيود الاقتصادية (ميزانية ١٠٠٠ دولار فقط)، العوامل البيئية المحلية، الحلول التكنولوجية البسيطة، الجوانب النفسية والاجتماعية للسكان، واستدامة الحل بعد عامين",
    'part2': "تعلم هذه القواعد الجديدة للعبة خلال دقيقتين ثم اشرح كيف ستفوز: اللعبة تتضمن ٣ لاعبين وألواح ملونة. كل لاعب يختار لونًا مختلفًا كل جولة. النقاط تحسب بناءً على ترتيب الألوان. هناك قواعد خاصة عندما يتطابق لونان.",
    'part3': "اخترع جهازًا باستخدام مواد معاد تدويرها فقط (زجاجات بلاستيك، أوراق، خيوط) لحل مشكلة تواجه سكان المناطق الحضرية الفقيرة. صف كيف يعمل ولماذا هذا الحل مبتكر وفعال.",
    'part4': "في هذا الموقف: مدير يصرخ على موظف أمام زملائه لأن مشروعًا تأخر. حلل المشاعر المختلفة لكل شخص حاضر، واقترح حلاً يصلح العلاقات مع الحفاظ على الإنتاجية.",
    'part5': "ارسم خطة لتعلم لغة جديدة في ٦ أشهر، مع تحديد: الموارد المجانية المتاحة، طريقة قياس التقدم، التحديات المتوقعة وكيفية التغلب عليها، وكيف ستتحدث مع متحدث أصلي بعد ٣ أشهر فقط.",
}

def run():
    sid = f'system_run_{os.getpid()}'
    start_session(sid)
    results = {}
    for pid, prompt in PROMPTS.items():
        print('\n' + '='*60)
        print(f'PART: {pid}\nPROMPT: {prompt}')
        resp = auto_route_and_respond(sid, prompt)
        engine = resp.get('engine') if isinstance(resp, dict) else None
        intent = resp.get('intent') if isinstance(resp, dict) else None
        reply = resp.get('reply_text') or resp.get('text') or ''
        print('\nEngine:', engine)
        print('Intent:', intent)
        print('Reply:')
        print(reply)
        results[pid] = {'engine': engine, 'intent': intent, 'reply': reply, 'raw': resp}

    out_path = os.path.join(ROOT, 'artifacts', 'agi_system_run_outputs.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print('\nSaved outputs to', out_path)

if __name__ == '__main__':
    run()
