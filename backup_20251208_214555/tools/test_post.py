import json
import urllib.request

payload = {'text': 'اختبر: {"text": "هذا نص منسق"}'}
req = urllib.request.Request('http://127.0.0.1:8000/chat', data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json; charset=utf-8'})
resp = urllib.request.urlopen(req, timeout=10)
body = resp.read().decode('utf-8', errors='replace')
print(body)
