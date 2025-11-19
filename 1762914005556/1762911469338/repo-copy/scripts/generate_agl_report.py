import json
import os
from typing import Any

IN_PATH = os.path.join('reports', 'agl_response_rerun.json')
OUT_TEXT = os.path.join('reports', 'agl_response_report.txt')
OUT_JSON = os.path.join('reports', 'agl_response_report_processed.json')


def extract_text_from_response(resp: Any) -> str:
    # Try common places the engine wrote content
    if not isinstance(resp, dict):
        return str(resp)
    # 1. answer.text
    ans = resp.get('answer', {})
    text = ans.get('text') if isinstance(ans, dict) else None
    if text:
        return text
    # 2. working.calls[*].engine_result
    working = resp.get('working', {})
    calls = working.get('calls', []) if isinstance(working, dict) else []
    parts = []
    for c in calls:
        er = c.get('engine_result') if isinstance(c, dict) else None
        if er is None:
            continue
        # if engine_result is a dict with textual fields, pretty-print
        if isinstance(er, dict):
            try:
                parts.append(json.dumps(er, ensure_ascii=False, indent=2))
            except Exception:
                parts.append(str(er))
        else:
            parts.append(str(er))
    if parts:
        return "\n---\n".join(parts)
    # 3. fallback: full JSON of resp
    try:
        return json.dumps(resp, ensure_ascii=False, indent=2)
    except Exception:
        return str(resp)


if __name__ == '__main__':
    if not os.path.exists(IN_PATH):
        print(f"Input file not found: {IN_PATH}")
        raise SystemExit(1)

    with open(IN_PATH, 'r', encoding='utf-8') as fh:
        data = json.load(fh)

    report_lines = []
    report_lines.append('تقرير AGL — ناتج إعادة التشغيل (ملخّص عربي)')
    report_lines.append('-------------------------------------------')

    parts = data.get('parts', [])
    for p in parts:
        part_id = p.get('part')
        report_lines.append(f'\nالجزء {part_id}:')
        # try to extract a readable block
        resp = p.get('response', {})
        text = extract_text_from_response(resp)
        report_lines.append(text)

    # evaluation
    report_lines.append('\n\nالتقييم النهائي:')
    eval_obj = data.get('evaluation', {})
    if eval_obj:
        eval_text = extract_text_from_response(eval_obj)
        report_lines.append(eval_text)
    else:
        report_lines.append('لا يوجد تقييم نهائي محفوظ.')

    full_report = '\n'.join(report_lines)

    # save text report
    os.makedirs(os.path.dirname(OUT_TEXT), exist_ok=True)
    with open(OUT_TEXT, 'w', encoding='utf-8') as fh:
        fh.write(full_report)

    # also save processed JSON for inspection
    with open(OUT_JSON, 'w', encoding='utf-8') as fh:
        json.dump({'report_text': full_report, 'raw': data}, fh, ensure_ascii=False, indent=2)

    # print to stdout
    print(full_report)
    print('\n(حفظت التقارير في:', OUT_TEXT, 'و', OUT_JSON, ')')
