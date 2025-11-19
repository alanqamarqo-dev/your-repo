import os
import json
try:
    import requests
except Exception:
    requests = None

base = os.getenv('AGL_LLM_BASEURL') or os.getenv('OLLAMA_API_URL') or 'http://localhost:11434'
model = os.getenv('AGL_LLM_MODEL') or os.getenv('AGL_OLLAMA_KB_MODEL') or 'qwen2.5:7b-instruct'

prompt_system = "أجب باللغة العربية الفصحى بجملة واحدة واضحة."
prompt_user = "قل: تم الاتصال بنجاح."

payload = {"model": model, "prompt": f"{prompt_system}\n\n{prompt_user}"}

print("Trying endpoints at:", base)
if requests is None:
    print("requests not installed in this environment. Install with: pip install requests")
    raise SystemExit(1)

# Try common endpoints for local LLM servers (tries several until one responds)
endpoints = [
    base,
    base.rstrip('/') + '/api/predict',
    base.rstrip('/') + '/api/generate',
    base.rstrip('/') + '/v1/complete',
    base.rstrip('/') + '/v1/predict',
]

for ep in endpoints:
    try:
        print('\nPOST ->', ep)
        r = requests.post(ep, json=payload, timeout=15)
        # If returned 405 method not allowed, try next
        if r.status_code == 405:
            print('  405 Method Not Allowed')
            continue
        r.raise_for_status()
        try:
            j = r.json()
            print('  Response JSON:', json.dumps(j, ensure_ascii=False, indent=2))
        except Exception:
            print('  Response text:', r.text)
        break
    except Exception as e:
        print('  Endpoint failed:', e)
else:
    print('\nLLM ping: no working endpoint found.\nTip: تأكد أن خدمة Ollama تعمل وأن النموذج مُثبّت (ollama pull <model>) أو أن AGL_LLM_BASEURL صحيح.')
