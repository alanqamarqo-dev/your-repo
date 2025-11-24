import urllib.request, json, time, random
BASE='http://127.0.0.1:8000/chat'
SID='web_test50'
# list of seed prompts
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
# Expand to 50 by random variations
msgs = []
while len(msgs) < 50:
    m = random.choice(seeds)
    # small randomization
    if random.random() < 0.2:
        m = m + ' ' + random.choice(['مزيد', 'تفصيل', 'بسيط', 'متقدم'])
    msgs.append(m)

opener = urllib.request.build_opener()
results = []
for i,msg in enumerate(msgs,1):
    payload = {'text': msg, 'session_id': SID}
    data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(BASE, data=data, headers={'Content-Type':'application/json; charset=utf-8'})
    print(f"{i:02d}. {msg}")
    try:
        with opener.open(req, timeout=15) as resp:
            body = resp.read().decode('utf-8')
            j = json.loads(body)
            print(' ->', j.get('meta', {}), ' reply:', (j.get('reply_text') or '')[:140])
            results.append((msg, j))
    except Exception as e:
        print(' -> Request failed', e)
    time.sleep(0.15)

# Save summary
with open('artifacts/run_50_results.json', 'w', encoding='utf-8') as f:
    json.dump([{'msg': m, 'resp': r} for m, r in results], f, ensure_ascii=False, indent=2)
print('Done. Saved artifacts/run_50_results.json')
