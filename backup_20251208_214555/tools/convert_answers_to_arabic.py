#!/usr/bin/env python3
"""Convert AGI test answers into direct Arabic answers by asking the local /chat endpoint

This script loads `artifacts/agi_full_test/agi_full_test_results.json`, then for each
item sends the original prompt + the system's answer to `POST /chat` with a strong
system instruction asking for a concise Arabic direct answer. Results are saved under
`artifacts/agi_full_test_ar/` as per-question JSON and a consolidated file.
"""

from __future__ import annotations
import json
import os
import time
from pathlib import Path
from typing import Dict, Any
import requests

ROOT = Path(__file__).resolve().parent.parent
IN_PATH = ROOT / 'artifacts' / 'agi_full_test' / 'agi_full_test_results.json'
OUT_DIR = ROOT / 'artifacts' / 'agi_full_test_ar'
OUT_DIR.mkdir(parents=True, exist_ok=True)

CHAT_URL = os.getenv('AGI_CHAT_URL', 'http://127.0.0.1:8000/chat')
TOKEN = os.getenv('GENESIS_ALPHA_TOKEN')


def load_results() -> Dict[str, Any]:
    with IN_PATH.open('r', encoding='utf-8') as f:
        return json.load(f)


def make_payload(prompt: str, system_instr: str) -> Dict[str, Any]:
    messages = [
        {"role": "system", "content": system_instr},
        {"role": "user", "content": prompt}
    ]
    return {"messages": messages}


def call_chat(payload: Dict[str, Any]) -> Dict[str, Any]:
    headers = {'Content-Type': 'application/json'}
    if TOKEN:
        headers['Authorization'] = f'Bearer {TOKEN}'
    resp = requests.post(CHAT_URL, json=payload, headers=headers, timeout=60)
    try:
        return resp.json()
    except Exception:
        return {"text": resp.text, "status_code": resp.status_code}


def sanitize_answer_text(txt: str) -> str:
    if not txt:
        return ''
    # Remove common header the system used
    txt = txt.replace('### 🧠 AGI Response (REVISED)', '')
    # remove repeated markers
    txt = txt.strip()
    return txt


def main():
    results = load_results()
    items = results.get('items', [])

    system_instr = (
        "أنت مترجم ومبسّط. مهمتك: اقرأ الإجابة الإنجليزية أو النص المعطى، "
        "وترجمها وأعد صياغتها بالعربية بصيغة مباشرة وموجزة لكل سؤال. "
        "أجب بالعربية فقط، وأعطِ إجابة مباشرة ومفصّلة حسب الحاجة، دون ملاحظات تشغيلية أو رؤوس." 
    )

    consolidated = {"session_id": results.get('session_id'), 'generated_at': time.time(), 'items': []}

    for it in items:
        qid = it.get('id')
        prompt = it.get('prompt','')
        original_answer = it.get('answer_text') or ''
        payload_prompt = (
            f"السؤال الأصلي:\n{prompt}\n\n" 
            f"إجابة النظام:\n{original_answer}\n\n"
            "الرجاء ترجمة هذه الإجابة إلى العربية وإعادة صياغتها كإجابة مباشرة ومباشرة للسؤال أعلاه."
        )

        payload = make_payload(payload_prompt, system_instr)
        try:
            resp = call_chat(payload)
        except Exception as e:
            resp = {"error": str(e)}

        # extract best text available
        answer_ar = None
        if isinstance(resp, dict):
            for k in ('reply', 'reply_text', 'answer', 'text', 'response'):
                if k in resp and resp[k]:
                    answer_ar = resp[k]
                    break
            if answer_ar is None and 'choices' in resp and isinstance(resp['choices'], list) and resp['choices']:
                c = resp['choices'][0]
                if isinstance(c, dict):
                    answer_ar = c.get('text') or c.get('message') or str(c)
                else:
                    answer_ar = str(c)
        if not answer_ar:
            answer_ar = resp.get('text') if isinstance(resp, dict) else str(resp)

        answer_ar = sanitize_answer_text(answer_ar)

        out = {
            'id': qid,
            'title': it.get('title'),
            'original_answer': original_answer,
            'answer_ar': answer_ar,
            'raw_chat_response': resp,
            'status_code': it.get('status_code')
        }

        with (OUT_DIR / f"{qid}.ar.json").open('w', encoding='utf-8') as fh:
            json.dump(out, fh, ensure_ascii=False, indent=2)

        consolidated['items'].append({'id': qid, 'file': f"{qid}.ar.json", 'title': it.get('title')})
        print(f"Converted {qid}")
        time.sleep(0.5)

    with (OUT_DIR / 'agi_full_test_results_ar.json').open('w', encoding='utf-8') as fh:
        json.dump(consolidated, fh, ensure_ascii=False, indent=2)

    print('\nDone. Arabic answers saved to:', OUT_DIR)


if __name__ == '__main__':
    main()
