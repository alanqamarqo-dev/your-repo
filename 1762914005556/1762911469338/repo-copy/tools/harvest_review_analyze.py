#!/usr/bin/env python3
"""Analyze artifacts/harvest_review.jsonl for rejection reasons and samples.

Usage: python tools/harvest_review_analyze.py [--file PATH]

Produces a summaryCounts and prints up to 10 samples per reason.
It attempts to detect common mojibake (windows-1252 bytes decoded as utf-8) and show a best-effort fix.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List


def try_fix_mojibake(s: str) -> str:
    """Heuristic: if the string contains many replacement characters or odd high-bytes, try re-encoding.
    This handles common windows-1252 -> utf-8 mojibake where bytes were incorrectly decoded.
    """
    if not s:
        return s
    # quick check for suspicious sequences (replacement char or percent of high codepoints)
    if '\ufffd' in s:
        # nothing to do, try fallback
        try:
            return s.encode('latin-1').decode('utf-8')
        except Exception:
            return s
    # if many characters are in the range typical for mojibake (0x80-0xFF displayed as two bytes)
    odd = sum(1 for ch in s if ord(ch) > 127)
    if odd / max(1, len(s)) > 0.15:
        try:
            return s.encode('latin-1').decode('utf-8')
        except Exception:
            return s
    return s


def load_lines(path: Path) -> List[Dict]:
    items = []
    malformed = 0
    with path.open('rb') as fh:
        for i, raw in enumerate(fh, start=1):
            try:
                line = raw.decode('utf-8').strip()
            except Exception:
                try:
                    # fallback: latin-1 decode then attempt to fix
                    line = raw.decode('latin-1').strip()
                except Exception:
                    malformed += 1
                    continue
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                # try to salvage common mojibake in the JSON text by re-decoding
                try:
                    obj = json.loads(line.encode('latin-1').decode('utf-8'))
                except Exception:
                    malformed += 1
                    continue
            items.append(obj)
    return items, malformed


def summarize(items: List[Dict]):
    by_reason: Dict[str, List[Dict]] = defaultdict(list)
    for it in items:
        reason = it.get('reason') or it.get('rejection') or 'unknown'
        by_reason[reason].append(it)

    print('\nFound {} review records across {} reason groups'.format(len(items), len(by_reason)))
    for reason, recs in sorted(by_reason.items(), key=lambda kv: -len(kv[1])):
        print('\n--- Reason: {} (count={})'.format(reason, len(recs)))
        samples = recs[:10]
        for s in samples:
            ts = s.get('ts')
            domain = s.get('domain') or ''
            source = s.get('source') or ''
            conf = s.get('confidence')
            text = s.get('text') or ''
            fixed_text = try_fix_mojibake(text)
            if fixed_text != text:
                note = ' (mojibake-fixed)'
            else:
                note = ''
            print('  - ts={} domain={} source={} conf={}{}'.format(ts, domain, source, conf, note))
            # print a short snippet of text
            snippet = fixed_text.replace('\n', ' ')[:300]
            print('    text: {}'.format(snippet))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--file', '-f', default='artifacts/harvest_review.jsonl')
    args = p.parse_args()
    path = Path(args.file)
    if not path.exists():
        print('File not found:', path)
        sys.exit(2)
    items, malformed = load_lines(path)
    print('Loaded {} records from {} (malformed skipped={})'.format(len(items), path, malformed))
    summarize(items)


if __name__ == '__main__':
    main()
