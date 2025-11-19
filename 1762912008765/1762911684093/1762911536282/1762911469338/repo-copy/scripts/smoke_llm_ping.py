"""Smoke-check for local LLM endpoints used by CI.

Usage example:
  python scripts/smoke_llm_ping.py --expect 200 --timeout 10

This script tries several common endpoints (base, /api/predict, /api/generate,
/v1/complete, /v1/predict) and returns exit code 0 if any responds with the
expected status (default 200). Prints helpful diagnostics.
"""
import os
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
_AGL_PREVIEW_1000 = _to_int('AGL_PREVIEW_1000', 1000)

try:
    import os
    def _to_int(name, default):
        try:
            return int(os.environ.get(name, str(default)))
        except Exception:
            return default
except Exception:
    def _to_int(name, default): return default
import sys
import argparse
import json
try:
    import requests
except Exception:
    requests = None
def main():
    p = argparse.ArgumentParser()
    p.add_argument('--expect', type=int, default=200, help='expected HTTP status code')
    p.add_argument('--timeout', type=int, default=10, help='request timeout seconds')
    p.add_argument('--base', type=str, default=os.getenv('AGL_LLM_BASEURL') or os.getenv('OLLAMA_API_URL') or 'http://localhost:11434', help='base URL to try')
    args = p.parse_args()
    if requests is None:
        print('requests not installed. Install with: pip install requests')
        return 2
    payload = {'model': os.getenv('AGL_LLM_MODEL') or os.getenv('AGL_OLLAMA_KB_MODEL') or 'qwen2.5:7b-instruct', 'prompt': 'أجب: تم الاتصال بنجاح.'}
    endpoints = [args.base, args.base.rstrip('/') + '/api/predict', args.base.rstrip('/') + '/api/generate', args.base.rstrip('/') + '/v1/complete', args.base.rstrip('/') + '/v1/predict']
    print(f'[smoke] trying endpoints at: {args.base}')
    for ep in endpoints:
        try:
            print(f'[smoke] POST -> {ep}')
            r = requests.post(ep, json=payload, timeout=args.timeout)
            print(f'[smoke] status: {r.status_code}')
            if r.status_code == args.expect:
                try:
                    j = r.json()
                    print('[smoke] response JSON:', json.dumps(j, ensure_ascii=False, indent=2))
                except Exception:
                    print('[smoke] response text:', r.text[:_AGL_PREVIEW_1000])
                print('[smoke] OK')
                return 0
            else:
                print(f'[smoke] unexpected status {r.status_code}; body: {r.text[:400]}')
        except Exception as e:
            print(f'[smoke] endpoint failed: {e}')
    print('\n[smoke] no working endpoint found.\nTip: ensure Ollama or other LLM server is running and model installed (ollama pull <model>) or set AGL_LLM_BASEURL correctly.')
    return 1
if __name__ == '__main__':
    sys.exit(main())
