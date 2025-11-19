import re, pathlib


def _find_call_args(text: str, start_idx: int) -> str | None:
    # given index of '(' after br.query, find matching ')' and return contents
    i = start_idx
    depth = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
            if depth == 0:
                # return inner args without surrounding parentheses
                return text[start_idx+1:i]
        i += 1
    return None


def test_no_or_queries_for_trace_and_type():
    bad = []
    for f in pathlib.Path('.').rglob('*.py'):
        # skip virtualenvs, caches, and this lint file itself
        if any(seg in f.parts for seg in ('.venv','__pycache__','site-packages','build','dist')):
            continue
        if f.name == 'test_no_or_queries_for_trace_and_type.py':
            continue
        txt = f.read_text(encoding='utf-8', errors='ignore')
        for m in re.finditer(r"br\.query\s*\(", txt):
            args = _find_call_args(txt, m.end()-1)
            if not args:
                continue
            has_type = re.search(r"\btype\s*=", args) is not None
            has_trace = re.search(r"\btrace_id\s*=", args) is not None
            has_match = re.search(r"\bmatch\s*=", args) is not None
            if has_type and has_trace and not has_match:
                bad.append(f"{f}: br.query({args.strip()[:200]})")
    assert not bad, "Found br.query(type=..., trace_id=...) without match='and' in:\n" + "\n".join(bad)
