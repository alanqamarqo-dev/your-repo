#!/usr/bin/env python3
"""Ingest free-reading text files into a simple KB JSON.

Reads UTF-8 text files from data/new_texts/, splits into sentences,
and writes `Knowledge_Base/FreeReads.json` and per-file artifacts.
This is intentionally simple — it creates atomic 'facts' as sentences
so downstream learners/harvesters can pick them up.
"""
import os, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IN_DIR = ROOT / 'data' / 'new_texts'
KB_DIR = ROOT / 'Knowledge_Base'
ART_DIR = ROOT / 'artifacts' / 'ingest'
IN_DIR.mkdir(parents=True, exist_ok=True)
KB_DIR.mkdir(parents=True, exist_ok=True)
ART_DIR.mkdir(parents=True, exist_ok=True)

SENT_RE = re.compile(r'(?<=\.|\?|!)\s+|\n+')

def split_sentences(text: str):
    # crude split preserving Arabic punctuation and line breaks
    parts = re.split(r'(?<=[\.\?\!\u061F\u061B])\s+', text.strip())
    return [p.strip() for p in parts if p.strip()]

def ingest_file(path: Path):
    txt = path.read_text(encoding='utf-8')
    sents = split_sentences(txt)
    out = {
        'source': str(path.relative_to(ROOT)),
        'n_sentences': len(sents),
        'sentences': sents,
    }
    art = ART_DIR / (path.stem + '.json')
    art.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    return out

def main():
    files = sorted(IN_DIR.glob('*.txt'))
    if not files:
        print('No text files found under', IN_DIR)
        return
    kb = []
    for f in files:
        print('Ingesting', f)
        out = ingest_file(f)
        for s in out['sentences']:
            kb.append({'source': out['source'], 'text': s})

    kb_path = KB_DIR / 'FreeReads.json'
    kb_path.write_text(json.dumps(kb, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Wrote KB with', len(kb), 'sentences ->', kb_path)

if __name__ == '__main__':
    main()
