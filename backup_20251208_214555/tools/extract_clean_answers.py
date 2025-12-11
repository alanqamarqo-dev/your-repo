import json
import re
from pathlib import Path

p = Path(__file__).resolve().parents[0] / '17_test_results.json'
if not p.exists():
    print('ERROR: results file not found:', p)
    raise SystemExit(1)

data = json.loads(p.read_text(encoding='utf-8'))

# Simple cleaning: remove AGI headers and Markdown, keep Arabic sentences.
hdr_re = re.compile(r"^###.*?\n\n", flags=re.S)
md_re = re.compile(r"\*\*|\*|`|```|> \*.*?$", flags=re.M)

for item in data:
    idx = item.get('q_index')
    q = item.get('question') or item.get('prompt') or ''
    resp = item.get('response') or {}
    # response may be dict or string
    if isinstance(resp, dict):
        text = resp.get('reply_text') or resp.get('reply') or json.dumps(resp, ensure_ascii=False)
    else:
        text = str(resp)

    # strip common AGI wrapper/header
    text = hdr_re.sub('', text).strip()
    # remove markdown-like artifacts
    text = md_re.sub('', text).strip()
    # normalize multiple blank lines
    text = re.sub(r"\n{2,}", "\n\n", text)

    print(f"--- السؤال {idx} ---")
    if q:
        print(q.strip())
    else:
        print("(السؤال غير متوفر)")
    print()
    print(text)
    print()

print('EXTRACTION_DONE')
