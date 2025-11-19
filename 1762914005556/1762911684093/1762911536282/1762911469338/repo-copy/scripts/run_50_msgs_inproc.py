from fastapi.testclient import TestClient
import sys, os
# ensure repo root is on path so we can import server module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import server
import json, random, time

BASE='/chat'
SID='web_test50_inproc'
seeds=[
    'اهلا',
    'ما هو عاصمة فرنسا؟',
    'احسب 12 * 34',
    'ما هو قانون نيوتن الثاني؟',
    'كيف اثبت Python على Windows؟',
    'ترجم hello إلى العربية',
    'أعطني 3 أفكار لتطبيق تعليمي',
    'ما هي سرعة الضوء؟',
    'ما سبب تغير الفصول؟',
    'كيف أقوم بتحميل ملف من الويب؟',
    'هل يمكنك كتابة سطر برمجي لطباعة Hello World؟',
    'لماذا السماء زرقاء؟',
    'ما هو تعريف الذكاء الاصطناعي؟',
    'احسب 999 + 1',
    'ما هي أكبر قارة؟',
    'كيف أصنع نسخة احتياطية لقاعدة بيانات؟',
    'أخبرني بنكتة قصيرة',
    'هل تفهم الرموز التعبيرية؟ 😊',
    'ما الفرق بين الطاقة والقدرة؟',
    'اقترح خطة لتعلم البرمجة خلال 3 أشهر',
]
msgs = []
while len(msgs) < 50:
    m = random.choice(seeds)
    if random.random() < 0.2:
        m = m + ' ' + random.choice(['مزيد', 'تفصيل', 'بسيط', 'متقدم'])
    msgs.append(m)

client = TestClient(server.app)
results = []
for i, msg in enumerate(msgs, 1):
    payload = {'text': msg, 'session_id': SID}
    print(f"{i:02d}. {msg}")
    try:
        r = client.post(BASE, json=payload)
        j = r.json()
        print(' ->', j.get('meta', {}), ' reply:', (j.get('reply_text') or '')[:140])
        results.append({'msg': msg, 'resp': j})
    except Exception as e:
        print(' -> Request failed', e)
    time.sleep(0.08)

with open('artifacts/run_50_results_inproc.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print('Done. Saved artifacts/run_50_results_inproc.json')
