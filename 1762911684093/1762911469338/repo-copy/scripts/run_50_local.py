# === AGL auto-injected knobs (idempotent) ===
try:
    import os
    def _to_int(name, default):
        try:
            return int(os.environ.get(name, str(default)))
        except Exception:
            return default
except Exception:
    def _to_int(name, default): return default
_AGL_PREVIEW_120 = _to_int('AGL_PREVIEW_120', 120)

try:
    import os
    def _to_int(name, default):
        try:
            return int(os.environ.get(name, str(default)))
        except Exception:
            return default
except Exception:
    def _to_int(name, default): return default
import json, random, os
import sys
sys.path.append(os.getcwd())
from Integration_Layer import Domain_Router
seeds = ['اهلا', 'ما هو عاصمة فرنسا؟', 'احسب 12 * 34', 'ما هو قانون نيوتن الثاني؟', 'كيف اثبت Python على Windows؟', 'ترجم hello إلى العربية', 'أعطني 3 أفكار لتطبيق تعليمي', 'ما هي سرعة الضوء؟', 'ما سبب تغير الفصول؟', 'كيف أقوم بتحميل ملف من الويب؟', 'هل يمكنك كتابة سطر برمجي لطباعة Hello World؟', 'لماذا السماء زرقاء؟', 'ما هو تعريف الذكاء الاصطناعي؟', 'احسب 999 + 1', 'ما هي أكبر قارة؟', 'كيف أصنع نسخة احتياطية لقاعدة بيانات؟', 'أخبرني بنكتة قصيرة', 'هل تفهم الرموز التعبيرية؟ 😊', 'ما الفرق بين الطاقة والقدرة؟', 'اقترح خطة لتعلم البرمجة خلال 3 أشهر']
msgs = []
while len(msgs) < 50:
    m = random.choice(seeds)
    if random.random() < 0.3:
        m = m + ' ' + random.choice(['مزيد', 'تفصيل', 'بسيط', 'متقدم', 'مقارنة'])
    msgs.append(m)
results = []
for i, m in enumerate(msgs, 1):
    r = Domain_Router.route(m)
    results.append({'msg': m, 'resp': r})
    print(f"{i:02d}. {m} -> {(r.get('reply_text') or r.get('text') or '')[:_AGL_PREVIEW_120]}")
out_path = os.path.join('artifacts', 'run_50_results_local.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print('Saved', out_path)
