#!/usr/bin/env python3
"""Generate a printable Markdown paper from unified_impossible_results.json

Usage: python generate_unified_paper.py
Writes: unified_impossible_report.md
"""
import json
from pathlib import Path
from datetime import datetime
import re

ROOT = Path(__file__).resolve().parent
INPUT = ROOT / 'unified_impossible_results.json'
OUTPUT = ROOT / 'unified_impossible_report.md'


def extract_streamed_response(text):
    """Try to recover readable text from streaming/json-line fragments.
    If the response is plain text, return as-is.
    If it's several JSON-lines like {"model":...,"response":"...","done":false}
    we collect the "response" fields and join them.
    """
    if not isinstance(text, str):
        return str(text)

    lines = [ln for ln in text.splitlines() if ln.strip()]
    # Fast path: if there are many lines that look like JSON objects, parse them
    responses = []
    parsed_any = False
    for ln in lines:
        ln = ln.strip()
        if ln.startswith('{') and '"response"' in ln:
            try:
                obj = json.loads(ln)
                if 'response' in obj:
                    responses.append(obj['response'])
                    parsed_any = True
                    continue
            except Exception:
                # try to extract via regex fallback
                m = re.search(r'"response"\s*:\s*"(.*)"\s*(,|})$', ln)
                if m:
                    responses.append(m.group(1))
                    parsed_any = True
                    continue
        # Another common pattern: lines that are clearly fragments (short)
        # fall back to accumulate them if we already parsed some
        if parsed_any:
            responses.append(ln)

    if parsed_any and responses:
        # join and unescape common escaped sequences if any
        joined = ''.join(responses)
        try:
            # fix escaped unicode sequences
            joined = bytes(joined, 'utf-8').decode('unicode_escape')
        except Exception:
            pass
        return joined

    # otherwise return original
    return text


def main():
    if not INPUT.exists():
        print(f"Input not found: {INPUT}")
        return 2

    data = json.load(INPUT.open(encoding='utf-8'))

    header = []
    header.append('# تقرير: إجابات اختبار "الأسئلة المستحيلة"')
    header.append(f'- مُولد في: {datetime.utcnow().isoformat()} UTC')
    header.append('')
    header.append('ملخص: الوثيقة تجمع الإجابات التي ولّدها نظام UnifiedAGISystem لجميع الأسئلة الستة عشر، كما خُزنَت في `unified_impossible_results.json`. بعض الاستجابات كانت متدفقة من محرك LLM ثم جُمعت هنا.')
    header.append('\n---\n')

    parts = list(header)

    for entry in data:
        qid = entry.get('id')
        title = entry.get('title')
        prompt = entry.get('prompt', '').strip()
        response = entry.get('response', {})
        final = response.get('final_response', '') if isinstance(response, dict) else response
        cleaned = extract_streamed_response(final)

        parts.append(f'## {qid}. {title}')
        parts.append('')
        parts.append('**السؤال (نص المطلوب):**')
        parts.append('\n```\n' + prompt + '\n```')
        parts.append('')
        parts.append('**الإجابة المستخلصة:**')
        parts.append('')
        parts.append(cleaned.strip() if cleaned else '_لم تُولَّد إجابة نصية واضحة._')
        parts.append('\n---\n')

    OUTPUT.write_text('\n'.join(parts), encoding='utf-8')
    print(f'Done. Report written to: {OUTPUT}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
