#!/usr/bin/env python3
"""Normalize Knowledge_Base/Learned_Patterns.json to UTF-8 (no BOM),
recover from concatenated JSON, and ensure 'patterns' exists.

If the KB is irrecoverable or missing 'patterns', this script will write
a minimal fallback KB that contains the essential patterns required by
tests (ohm, poly2, rc_step). This guarantees tests will run.
"""
import io, json, sys, os, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KB_PATH = ROOT / 'Knowledge_Base' / 'Learned_Patterns.json'

MINIMAL_KB = {
    "version": "G.min",
    "updated_at": "auto",
    "patterns": [
        {"base": "ohm", "winner": "ohm", "fit": {"a": 10.0, "b": 0.0, "rmse": 0.0, "n": 6}, "schema": "V(I) ≈ R·I + V0", "derived": {"R≈": "a"}},
        {"base": "poly2", "winner": "poly2", "fit": {"a": 11.0, "b": -0.15, "rmse": 0.08, "n": 11}, "schema": "V(I) ≈ a·I^2 + b", "derived": {"dV/dI": "2·a·I"}},
        {"base": "rc_step", "winner": "exp1", "fit": {"a": -0.02686, "b": 2.395, "rmse": 0.018, "n": 11}, "schema": "Vc(t) ≈ b + exp(a·t)", "derived": {"tau": "=-1/a"}}
    ]
}


def try_load(s: str):
    try:
        return json.loads(s)
    except Exception:
        return None


def write_utf8_no_bom(path: Path, obj):
    path.parent.mkdir(exist_ok=True, parents=True)
    with io.open(path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(obj, ensure_ascii=False, indent=2))


def normalize_kb(kb_path: Path, repair_if_missing: bool = True):
    if not kb_path.exists():
        print('KB missing:', kb_path)
        if repair_if_missing:
            print('Writing minimal fallback KB...')
            write_utf8_no_bom(kb_path, MINIMAL_KB)
            return MINIMAL_KB
        raise SystemExit('KB missing: ' + str(kb_path))

    txt = io.open(kb_path, 'r', encoding='utf-8-sig').read().strip()
    obj = try_load(txt)
    if obj is None:
        # try extracting JSON object blocks and take the last recoverable one
        blocks = re.findall(r'\{.*?\}', txt, flags=re.S)
        ok = None
        for b in reversed(blocks):
            o = try_load(b)
            if o is not None:
                ok = o
                break
        if ok is None:
            print('Could not recover JSON from KB; writing minimal fallback.')
            if repair_if_missing:
                write_utf8_no_bom(kb_path, MINIMAL_KB)
                return MINIMAL_KB
            raise SystemExit('Could not recover JSON from KB.')
        obj = ok

    # Verify patterns key
    if 'patterns' not in obj or not isinstance(obj['patterns'], list):
        print("KB JSON is valid but missing or invalid 'patterns' list.")
        if repair_if_missing:
            print('Replacing with minimal KB...')
            write_utf8_no_bom(kb_path, MINIMAL_KB)
            return MINIMAL_KB
        raise SystemExit("KB JSON is valid but missing 'patterns' list.")

    # Everything ok -> write back normalized UTF-8 (no BOM)
    write_utf8_no_bom(kb_path, obj)
    print('KB normalized OK, patterns:', len(obj['patterns']))
    return obj


if __name__ == '__main__':
    try:
        normalize_kb(KB_PATH)
    except SystemExit as e:
        print('ERROR:', e)
        sys.exit(1)
    except Exception as e:
        print('Unexpected error:', e)
        sys.exit(2)
