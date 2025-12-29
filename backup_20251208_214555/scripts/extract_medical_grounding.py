import argparse
import json
import os
import re
from typing import List, Optional

JSONL = os.path.join(os.getcwd(), 'artifacts', 'medical_queries.jsonl')
OUT_DEFAULT = os.path.join(os.getcwd(), 'artifacts', 'medical_grounding_report.txt')


def read_last_n(path: str, n: int = 3) -> List[dict]:
    if not os.path.exists(path):
        return []
    with open(path, 'rb') as f:
        # read lines in reverse
        f.seek(0, os.SEEK_END)
        size = f.tell()
        block = 1024
        data = b''
        lines = []
        while len(lines) <= n and size > 0:
            read_from = max(0, size - block)
            f.seek(read_from)
            chunk = f.read(size - read_from)
            data = chunk + data
            lines = data.splitlines()
            size = read_from
        lines = [l.decode('utf-8', errors='replace') for l in lines if l.strip()]
        return [json.loads(l) for l in lines[-n:]]


def _collect_long_strings_from_obj(obj):
    parts = []
    if isinstance(obj, str):
        if len(obj) > 80:
            parts.append(obj)
        return parts
    if isinstance(obj, dict):
        for v in obj.values():
            parts.extend(_collect_long_strings_from_obj(v))
    if isinstance(obj, list):
        for v in obj:
            parts.extend(_collect_long_strings_from_obj(v))
    return parts


def extract_rag_snippet(answer: str, provenance: dict = None) -> str:
    """Try multiple heuristics to extract the RAG-provided snippet.

    1) Look for common marker variants in the final answer text.
    2) If not found, inspect provenance for long retrieved passages.
    """
    if not answer and not provenance:
        return ''

    if answer:
        markers = [
            '[مقتطفات من ذاكرة RAG]',
            'مقتطفات من ذاكرة RAG',
            'مقتطف من ذاكرة RAG',
            '[RAG snippets]',
            'RAG snippet',
        ]
        for marker in markers:
            idx = answer.find(marker)
            if idx != -1:
                start = idx + len(marker)
                end_markers = ['=== ملخص الأنظمة الداخلية', '=== JSON كامل للـ provenance', '=== ملخص', '\n\n']
                end = None
                for m in end_markers:
                    j = answer.find(m, start)
                    if j != -1:
                        end = j
                        break
                if end is None:
                    end = min(len(answer), start + 1500)
                snippet = answer[start:end].strip()
                if snippet:
                    return snippet

    # fallback: look into provenance for long retrieved texts
    if provenance:
        parts = _collect_long_strings_from_obj(provenance)
        if parts:
            # prefer the longest candidate
            parts = sorted(parts, key=lambda s: len(s), reverse=True)
            for p in parts:
                # heuristics: skip things that look like JSON/provenance dumps
                if len(p) < 80:
                    continue
                # return first long candidate
                return p.strip()

    return ''


def find_char_matches(answer: str, snippet: str, provenance_text: str = None) -> List[dict]:
    """Find character-level matches of `snippet` inside `answer`.

    If direct match fails, try sliding-window substring matching with decreasing
    window sizes. If that also fails, try extracting long substrings from
    `provenance_text` and then searching those in the answer.
    """
    if not snippet or not answer:
        return []

    # direct exact match
    idx = answer.find(snippet)
    if idx != -1:
        return [{'start': idx, 'end': idx + len(snippet), 'match_len': len(snippet)}]

    s = snippet
    L = len(s)
    best = {'start': -1, 'end': -1, 'match_len': 0, 'fragment': ''}

    # sliding-window search: try larger windows first, slide by 1 for accuracy
    max_w = min(200, L)
    min_w = 30
    for w in range(max_w, min_w - 1, -5):
        for i in range(0, L - w + 1):
            part = s[i:i + w]
            j = answer.find(part)
            if j != -1 and w > best['match_len']:
                best = {'start': j, 'end': j + w, 'match_len': w, 'fragment': part}
        if best['match_len']:
            break

    # if nothing found, try to match via provenance_text: find long substrings there,
    # then attempt to locate them inside the answer
    if not best['match_len'] and provenance_text:
        P = provenance_text
        # take long parts from provenance and attempt to locate in answer
        cand_len = min(300, len(P))
        for w in range(cand_len, min_w - 1, -20):
            for i in range(0, len(P) - w + 1, 10):
                part = P[i:i + w]
                if len(part.strip()) < 40:
                    continue
                j = answer.find(part)
                if j != -1 and w > best['match_len']:
                    best = {'start': j, 'end': j + w, 'match_len': w, 'fragment': part}
            if best['match_len']:
                break

    if best['match_len']:
        return [{'start': best['start'], 'end': best['end'], 'match_len': best['match_len']}]
    return []


def main(max_chars: Optional[int] = 2000, out_path: Optional[str] = None, n: int = 3):
    parser = None
    # entries
    entries = read_last_n(JSONL, n)
    if not entries:
        print('no entries found in', JSONL)
        return
    rows = []
    for e in entries:
        q = e.get('user_question') or e.get('full_question') or e.get('question') or ''
        ans = e.get('answer') or e.get('reply') or ''
        prov = e.get('provenance', {}) or {}
        # try to extract snippet from answer first, then from provenance
        rag_snip = extract_rag_snippet(ans, provenance=prov)
        # prepare a joined provenance text to help matching heuristics
        prov_text = None
        try:
            parts = _collect_long_strings_from_obj(prov)
            if parts:
                prov_text = '\n\n'.join(parts)
        except Exception:
            prov_text = None

        matches = find_char_matches(ans, rag_snip, provenance_text=prov_text) if rag_snip else []
        rows.append({'question': q, 'answer': ans, 'rag_snippet': rag_snip, 'matches': matches, 'raw_provenance': prov})

    # write a human-readable report
    out_file = out_path or OUT_DEFAULT
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write('Medical RAG grounding report\n')
        f.write('=' * 60 + '\n\n')
        for i, r in enumerate(rows, 1):
            f.write(f'Record #{i}\n')
            f.write('-' * 40 + '\n')
            f.write('Question:\n')
            f.write(r['question'] + '\n\n')
            if max_chars is None:
                f.write('Final Answer (full text):\n')
                f.write(r['answer'] + '\n\n')
            else:
                f.write(f'Final Answer (trimmed {max_chars} chars):\n')
                trimmed = (r['answer'][:max_chars] + ('...' if len(r['answer'])>max_chars else ''))
                f.write(trimmed + '\n\n')
            f.write('Extracted RAG Snippet (if any):\n')
            f.write((r['rag_snippet'] or '<none>') + '\n\n')
            f.write('Provenance (raw):\n')
            try:
                f.write(json.dumps(r['raw_provenance'], ensure_ascii=False, indent=2) + '\n')
            except Exception:
                f.write(str(r['raw_provenance']) + '\n')
            f.write('\n')
            f.write('Character-level matches (snippet -> answer):\n')
            if r['matches']:
                for m in r['matches']:
                    f.write(f"- start={m['start']} end={m['end']} match_len={m['match_len']}\n")
                    context = r['answer'][max(0, m['start']-40):m['end']+40]
                    f.write('  context preview:\n')
                    f.write(context + '\n')
            else:
                f.write('- none found\n')
            f.write('\n\n')
    print('wrote report to', out_file)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Extract RAG grounding report from medical queries JSONL')
    ap.add_argument('--no-trim', action='store_true', help='Do not trim final answers in the report (output full text)')
    ap.add_argument('--max-chars', type=int, default=2000, help='Max chars to trim final answer to (ignored if --no-trim)')
    ap.add_argument('--out', type=str, default=None, help='Output report path')
    ap.add_argument('-n', type=int, default=3, help='Number of last entries to read from JSONL')
    args = ap.parse_args()
    max_chars = None if args.no_trim else args.max_chars
    main(max_chars=max_chars, out_path=args.out, n=args.n)
