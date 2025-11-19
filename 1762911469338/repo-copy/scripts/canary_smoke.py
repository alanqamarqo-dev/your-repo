"""Daily canary smoke script.
Runs 3 short Arabic prompts through Hosted_LLM and writes results to
artifacts/reports/canary.json (single-run summary: timestamp, questions, answers,
latencies, pass/fail flags).

Checks performed:
- Response contains Arabic letters.
- Response length is > 1 and <= 200 characters.
- Latency below threshold (default 8s per question, configurable via env AGL_CANARY_MAX_LAT_SEC)

Designed to be safe, fast, and side-effect free.
"""
from __future__ import annotations
import json
import os
import re
import time
from typing import List, Dict, Any

# local imports
from Integration_Layer.Hybrid_Composer import build_prompt_context
from Core_Engines.Hosted_LLM import chat_llm

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'artifacts', 'reports')
os.makedirs(OUT_DIR, exist_ok=True)
OUT_PATH = os.path.join(OUT_DIR, 'canary.json')

QUESTIONS: List[str] = [
    "ما هي عاصمة مصر؟",
    "كم عدد أيام الأسبوع؟",
    "ما لون السماء في النهار؟",
]

AR_LETTER_RE = re.compile(r"[\u0600-\u06FF]")
MAX_LAT = float(os.environ.get('AGL_CANARY_MAX_LAT_SEC', '8.0'))

results: List[Dict[str, Any]] = []
start_run = int(time.time())
all_ok = True

for q in QUESTIONS:
    msg = build_prompt_context(story="", questions=q)
    t0 = time.time()
    try:
        resp = chat_llm(msg, max_new_tokens=128, temperature=0.05, top_p=0.3)
        latency = time.time() - t0
        text = (resp.get('text') or '') if isinstance(resp, dict) else str(resp)
        text = text.strip()
        has_ar = bool(AR_LETTER_RE.search(text))
        length_ok = 1 < len(text) <= 200
        latency_ok = latency <= MAX_LAT
        ok = bool(has_ar and length_ok and latency_ok)
        results.append({'question': q, 'answer': text, 'latency_s': round(latency, 3), 'has_arabic': has_ar, 'length_ok': length_ok, 'latency_ok': latency_ok, 'ok': ok})
        all_ok = all_ok and ok
    except Exception as e:
        latency = time.time() - t0
        results.append({'question': q, 'answer': '', 'latency_s': round(latency,3), 'error': str(e), 'ok': False})
        all_ok = False

out = {
    'ts': start_run,
    'all_ok': all_ok,
    'max_latency_s': MAX_LAT,
    'results': results,
}

# write a timestamped artifact (overwrite previous canary.json)
try:
    with open(OUT_PATH, 'w', encoding='utf-8') as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
    print(f"Wrote canary report to {OUT_PATH}")
except Exception as e:
    print(f"Failed to write canary report: {e}")

# exit code (non-zero when failing could be used by scheduler)
if not all_ok:
    raise SystemExit(2)
else:
    print("Canary OK")
