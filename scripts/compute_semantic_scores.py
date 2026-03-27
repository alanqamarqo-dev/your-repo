#!/usr/bin/env python3
"""Compute semantic similarity scores between mission answers and reference answers.
Writes CSV to `artifacts/mission_eval_with_scores.csv`.

Fallback behavior: if `sentence_transformers` is installed, use it to compute embeddings
and cosine similarity. Otherwise use `difflib.SequenceMatcher` ratio as a cheap fallback.
"""
import argparse
import json
import os
import csv
import sys
from math import sqrt

ARTIFACT_DEFAULT = os.path.join('artifacts', 'mission_direct_results.json')
REFS = os.path.join('scripts', 'agi_evaluation_references.json')
OUT_DEFAULT = os.path.join('artifacts', 'mission_eval_with_scores.csv')


def safe_load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def try_sentence_transformers():
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np
        model = SentenceTransformer('all-MiniLM-L6-v2')
        return model
    except Exception:
        return None


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = sqrt(sum(x * x for x in a))
    nb = sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def fallback_ratio(a, b):
    import difflib
    return difflib.SequenceMatcher(None, a, b).ratio()


def extract_text(answer_entry):
    # answer_entry may be a dict or string
    if isinstance(answer_entry, dict):
        # Common shapes: {'answer': '...'} or {'message': {'content': '...'}}
        for key in ('answer', 'text', 'content', 'message'):
            if key in answer_entry:
                val = answer_entry[key]
                if isinstance(val, dict) and 'content' in val:
                    return val.get('content', '')
                if isinstance(val, str):
                    return val
        # fallback to str()
        return json.dumps(answer_entry, ensure_ascii=False)
    return str(answer_entry)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--artifact', default=ARTIFACT_DEFAULT, help='Path to mission results JSON')
    p.add_argument('--out', default=OUT_DEFAULT, help='Output CSV path')
    args = p.parse_args()

    ARTIFACT = args.artifact
    OUT = args.out

    if not os.path.exists(ARTIFACT):
        print(f'Error: mission artifact not found: {ARTIFACT}', file=sys.stderr)
        sys.exit(2)
    if not os.path.exists(REFS):
        print(f'Warning: references file not found: {REFS}', file=sys.stderr)

    results = safe_load_json(ARTIFACT)
    refs = {}
    if os.path.exists(REFS):
        refs = safe_load_json(REFS)

    model = try_sentence_transformers()
    use_embed = model is not None
    if use_embed:
        print('Using sentence-transformers for embeddings')
    else:
        print('sentence-transformers not available; using difflib fallback')

    rows = []
    texts = []
    ref_texts = []

    # build lists for embeddings if available
    for entry in results.get('results', results if isinstance(results, list) else []):
        qid = entry.get('id') if isinstance(entry, dict) else None
        ans = extract_text(entry.get('answer') if isinstance(entry, dict) else entry)
        texts.append((qid, ans, entry.get('rt') if isinstance(entry, dict) else None))
        # find reference
        ref = refs.get(qid) if isinstance(refs, dict) else None
        if ref is None and isinstance(entry, dict):
            # try numeric id
            ref = refs.get(str(qid)) if isinstance(refs, dict) else None
        ref_texts.append(ref if ref is not None else '')

    if use_embed:
        # prepare lists
        cand_texts = [t[1] for t in texts]
        ref_concat = [str(r) for r in ref_texts]
        cand_emb = model.encode(cand_texts, convert_to_numpy=True)
        ref_emb = model.encode(ref_concat, convert_to_numpy=True)
        for (qid, ans, rt), rtext, cemb, remb in zip(texts, ref_texts, cand_emb, ref_emb):
            score = float(cosine(cemb.tolist(), remb.tolist()))
            rows.append((qid, ans, rtext, rt, score))
    else:
        for (qid, ans, rt), rtext in zip(texts, ref_texts):
            score = fallback_ratio(ans, str(rtext))
            rows.append((qid, ans, rtext, rt, score))

    os.makedirs(os.path.dirname(OUT) or 'artifacts', exist_ok=True)
    with open(OUT, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(('id', 'answer', 'reference', 'rt_s', 'semantic_score'))
        for r in rows:
            w.writerow([r[0], r[1], r[2], r[3], r[4]])

    print(f'Wrote scores to {OUT}')


if __name__ == '__main__':
    main()
