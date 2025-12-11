import sys, os, re
# ensure repo root on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Self_Improvement.hosted_llm_adapter import HostedLLMAdapter
import json


def _strip_ansi(s: str) -> str:
    return re.sub(r'\x1B[@-_][0-?]*[ -/]*[@-~]', '', s)


def _extract_json_array_from_text(s: str):
    if not isinstance(s, str):
        return None
    clean = _strip_ansi(s)
    # try direct parse
    try:
        parsed = json.loads(clean)
        if isinstance(parsed, list):
            return parsed
    except Exception:
        pass

    # look for first bracketed JSON array
    m = re.search(r'(\[.*\])', clean, re.DOTALL)
    if not m:
        return None
    candidate = m.group(1)
    # remove newlines that split words (unicode-aware)
    candidate_fixed = re.sub(r'(?<=\w)\n(?=\w)', '', candidate)
    # fix newlines splitting decimal numbers like 0\n.9
    candidate_fixed = re.sub(r'(?<=\d)\n(?=[\.\d])', '', candidate_fixed)
    # remove stray control chars
    candidate_fixed = re.sub(r'[\x00-\x1F]+', ' ', candidate_fixed)
    try:
        data = json.loads(candidate_fixed)
        if isinstance(data, list):
            return data
    except Exception:
        pass

    # try swapping single quotes
    try:
        alt = candidate_fixed.replace("'", '"')
        data = json.loads(alt)
        if isinstance(data, list):
            return data
    except Exception:
        pass

    # repair attempt: if there's an opening '[' but no closing ']', try to close at last '}'
    first_br = clean.find('[')
    last_br = clean.rfind(']')
    if first_br != -1 and last_br <= first_br:
        last_obj = clean.rfind('}')
        if last_obj != -1 and last_obj > first_br:
            repaired = clean[first_br:last_obj+1] + ']'
            repaired = re.sub(r'(?<=\w)\n(?=\w)', '', repaired)
            repaired = re.sub(r'(?<=\d)\n(?=[\.\d])', '', repaired)
            repaired = re.sub(r'[\x00-\x1F]+', ' ', repaired)
            try:
                data = json.loads(repaired)
                if isinstance(data, list):
                    return data
            except Exception:
                try:
                    alt = repaired.replace("'", '"')
                    data = json.loads(alt)
                    if isinstance(data, list):
                        return data
                except Exception:
                    pass

    return None


h = HostedLLMAdapter()
print('HostedLLMAdapter instantiated; fast_mode=', getattr(h, 'fast_mode', None))
try:
    task = {'question': '[TEST] Return a JSON array: [{"hypothesis":"test","confidence":0.9,"reasoning":"r"}]', 'deep_mode': False}
    r = h.process_task(task, timeout_s=10)
    # try to normalize various shapes and extract a JSON list
    extracted = None
    print('TYPE (raw):', type(r))
    if isinstance(r, dict):
        print('REPR keys:', list(r.keys()))
        content = r.get('content') or {}
        # build a textual blob from likely fields
        parts = []
        if isinstance(content, dict):
            for k in ('answer', 'reasoning', 'reasoning_long', 'note', 'improved_answer'):
                v = content.get(k)
                if isinstance(v, str) and v.strip():
                    parts.append(v.strip())
        elif isinstance(content, str):
            parts.append(content)

        # also check verified.improved_answer if present
        verified = None
        if isinstance(content, dict):
            verified = content.get('verified') or {}
            if isinstance(verified, dict):
                ia = verified.get('improved_answer')
                if isinstance(ia, str) and ia.strip():
                    parts.append(ia.strip())

        blob = "\n".join(parts) if parts else str(content)
        print('CONTENT preview:', repr(blob)[:2000])
        extracted = _extract_json_array_from_text(blob)
    else:
        txt = str(r)
        print('RAW repr:', repr(txt)[:2000])
        extracted = _extract_json_array_from_text(txt)

    if extracted is not None:
        print('TYPE:', type(extracted))
        print('EXTRACTED:', extracted)
    else:
        print('No JSON array extracted from response.')
except Exception as e:
    print('CALL_ERROR:', e)
