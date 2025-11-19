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
import urllib.request, json, time, sys
BASE = 'http://127.0.0.1:8000/chat'
SID = 'web_test10'
messages = ['اهلا', 'Hello', 'ما هو عاصمة فرنسا؟', 'احسب 123 * 45', 'أخبرني بنبذة قصيرة عن الذكاء الاصطناعي', 'هذا نص طويل للاختبار: ' + 'البيانات ' * 30, '', 'كيف يمكنني تحميل ملف وتخزينه؟', '😊 هل تفهم الرموز التعبيرية؟', 'أعطني قائمة بخطوات تثبيت Python على Windows']
opener = urllib.request.build_opener()
for i, msg in enumerate(messages, 1):
    payload = {'text': msg, 'session_id': SID}
    data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(BASE, data=data, headers={'Content-Type': 'application/json; charset=utf-8'})
    print(f'--- Message {i} -> {repr(msg)[:_AGL_PREVIEW_120]}')
    try:
        with opener.open(req, timeout=15) as resp:
            body = resp.read().decode('utf-8')
            try:
                j = json.loads(body)
            except Exception:
                j = {'raw': body}
            print('Response:', json.dumps(j, ensure_ascii=False, indent=2))
    except Exception as e:
        print('Request failed:', e)
    time.sleep(0.2)
import os
p = os.path.join('sessions', f'{SID}.json')
print('\n--- Persisted session file:', p)
if os.path.exists(p):
    with open(p, 'r', encoding='utf-8') as f:
        print(f.read())
else:
    print('Session file not found')
