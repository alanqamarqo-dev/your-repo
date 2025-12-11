import os
from Self_Improvement.hosted_llm_adapter import HostedLLMAdapter
import requests
h=HostedLLMAdapter()
print('BASE_URL=', h.base_url)
urls = ['/api/chat','/api/generate','/v1/chat/completions','/v1/completions']
for p in urls:
    url = h.base_url.rstrip('/') + p
    print('TRY', url)
    try:
        r = requests.post(url, json={"model": h.model, "messages": [{"role":"user","content":"اختبار"}], "stream": False}, timeout=5)
        print('STATUS', r.status_code)
        print('TEXT_SNIPPET', r.text[:400])
    except Exception as e:
        print('ERR', repr(e))
