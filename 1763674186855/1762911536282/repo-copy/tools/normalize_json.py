#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def normalize_file(path: Path, rewrite: bool = False):
    raw = path.read_bytes()
    try:
        # decode with utf-8-sig to tolerate BOM
        text = raw.decode('utf-8-sig')
    except Exception:
        # fallback: try utf-8
        text = raw.decode('utf-8', errors='ignore')
    # attempt to parse first JSON object to eliminate trailing garbage
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        # try to find the first JSON object using raw_decode
        dec = json.JSONDecoder()
        try:
            obj, idx = dec.raw_decode(text)
        except Exception:
            return False, 'invalid-json'
    # re-serialize with stable formatting
    out_text = json.dumps(obj, ensure_ascii=False, indent=2) + '\n'
    out_bytes = out_text.encode('utf-8')
    if out_bytes != raw:
        if rewrite:
            path.write_bytes(out_bytes)
            return True, 'rewritten'
        else:
            return True, 'would-rewrite'
    return False, 'ok'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true', help='Only check; exit nonzero if any file needs normalization')
    ap.add_argument('paths', nargs='*', help='Files or folders to scan (defaults to Knowledge_Base and repo root json)')
    args = ap.parse_args()

    targets = []
    if args.paths:
        for p in args.paths:
            targets.append(Path(p))
    else:
        targets = [Path('Knowledge_Base'), Path('.')]

    changed = []
    problems = 0
    for t in targets:
        if t.is_file() and t.suffix.lower() == '.json':
            ok, status = normalize_file(t, rewrite=not args.check)
            if ok:
                changed.append((str(t), status))
        elif t.is_dir():
            for p in t.rglob('*.json'):
                ok, status = normalize_file(p, rewrite=not args.check)
                if ok:
                    changed.append((str(p), status))

    for f, s in changed:
        print(f'{s}: {f}')
    if args.check and changed:
        print('\nNormalization required for {} files'.format(len(changed)))
        raise SystemExit(2)
    if not changed:
        print('All JSON files already normalized')


if __name__ == '__main__':
    main()
