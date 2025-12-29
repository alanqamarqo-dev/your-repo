#!/usr/bin/env python3
"""Postprocess harvested candidates: apply quality gates and write accepted/rejected records.

Usage: python tools/harvest_postprocess.py [--candidates <path>] [--min-confidence 0.7] [--max-text-len 1000]

Behavior:
- Reads candidates from --candidates (JSONL) or from artifacts/external_info_cache/*.json (fallback)
- Gates: confidence >= min_confidence, non-empty source, domain allowed (if configs/harvest_plan.yaml exists), text length <= max_text_len
- Dedup: checks existing artifacts/harvested_facts.jsonl and in-run set by (domain, normalized_text)
- Writes accepted to artifacts/harvested_facts.jsonl
- Writes rejected to artifacts/harvest_review.jsonl with reason
- Updates artifacts/harvest_progress.json (per-domain accepted counts)
"""

import argparse
import json
import os
import glob
import sys
import time
from collections import defaultdict
import hashlib

REPO = os.getcwd()
CACHE_DIR = os.environ.get('AGL_EXTERNAL_INFO_CACHE_DIR') or os.path.join(REPO, 'artifacts', 'external_info_cache')
HARVESTED_PATH = os.path.join(REPO, 'artifacts', 'harvested_facts.jsonl')
REVIEW_PATH = os.path.join(REPO, 'artifacts', 'harvest_review.jsonl')
PROGRESS_PATH = os.path.join(REPO, 'artifacts', 'harvest_progress.json')
PLAN_PATH = os.path.join(REPO, 'configs', 'harvest_plan.yaml')


def load_allowed_domains():
    domains = None
    try:
        import yaml
        if os.path.exists(PLAN_PATH):
            with open(PLAN_PATH, 'r', encoding='utf-8') as fh:
                cfg = yaml.safe_load(fh)
                # expect mapping of domain->target
                if isinstance(cfg, dict):
                    domains = set(cfg.keys())
    except Exception:
        domains = None
    return domains


def normalize_text(t: str) -> str:
    if t is None: return ''
    s = ' '.join(str(t).split())
    return s


def try_fix_mojibake(s: str) -> str:
    if not s:
        return s
    # heuristic: if many high-codepoints, try latin-1 -> utf-8
    try:
        odd = sum(1 for ch in s if ord(ch) > 127)
    except Exception:
        return s
    if odd / max(1, len(s)) > 0.12:
        try:
            return s.encode('latin-1').decode('utf-8')
        except Exception:
            return s
    return s


def key_of(f):
    return (f.get('domain','').strip(), normalize_text(f.get('text','')))


def read_candidates_from_cache():
    out = []
    if not os.path.isdir(CACHE_DIR):
        return out
    for p in sorted(glob.glob(os.path.join(CACHE_DIR, '*.json'))):
        try:
            with open(p, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
                if isinstance(data, list):
                    out.extend(data)
                elif isinstance(data, dict):
                    # if dict contains 'facts' key
                    if 'facts' in data and isinstance(data['facts'], list):
                        out.extend(data['facts'])
                    else:
                        out.append(data)
        except Exception:
            continue
    return out


def read_candidates_from_file(path):
    out = []
    try:
        with open(path, 'r', encoding='utf-8') as fh:
            for line in fh:
                line=line.strip()
                if not line: continue
                try:
                    obj = json.loads(line)
                    # attempt to fix mojibake in text/source/domain
                    if isinstance(obj, dict):
                        if 'text' in obj and isinstance(obj['text'], str):
                            obj['text'] = try_fix_mojibake(obj['text'])
                        if 'source' in obj and isinstance(obj['source'], str):
                            obj['source'] = try_fix_mojibake(obj['source'])
                        if 'domain' in obj and isinstance(obj['domain'], str):
                            obj['domain'] = try_fix_mojibake(obj['domain'])
                    out.append(obj)
                except Exception:
                    continue
    except Exception:
        pass
    return out


def load_existing_keys():
    seen = set()
    if not os.path.exists(HARVESTED_PATH):
        return seen
    try:
        with open(HARVESTED_PATH, 'r', encoding='utf-8') as fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                    k = (rec.get('domain','').strip(), normalize_text(rec.get('text','')))
                    seen.add(k)
                except Exception:
                    continue
    except Exception:
        pass
    return seen


def append_jsonl(path, rec):
    try:
        with open(path, 'a', encoding='utf-8') as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + '\n')
    except Exception:
        print('WARN: failed to write', path, file=sys.stderr)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidates', help='JSONL file of candidate facts (optional)')
    parser.add_argument('--min-confidence', type=float, default=0.7)
    parser.add_argument('--dedupe-strict', action='store_true', help='apply strict dedupe (default: in-run+existing)')
    parser.add_argument('--max-text-len', type=int, default=1000)
    args = parser.parse_args()

    candidates = []
    if args.candidates and os.path.exists(args.candidates):
        candidates = read_candidates_from_file(args.candidates)
    else:
        candidates = read_candidates_from_cache()

    if not candidates:
        print('No candidates found; nothing to postprocess')
        return 0

    allowed_domains = load_allowed_domains()
    existing = load_existing_keys()
    inrun = set()

    # simple mapping from common source strings to domains (can be extended)
    source_domain_map = {
        'chemistry.org': 'chemistry.organic',
        'chemistry.org.uk': 'chemistry.organic',
        'physics textbooks': 'physics.classical',
        'physics for scientists': 'physics.classical',
        'mubabra': 'electricity.basics'
    }

    counts = defaultdict(int)
    accepted = []
    rejected = []

    for f in candidates:
        # normalize and attempt fixes
        domain = (f.get('domain') or '').strip()
        text = normalize_text(f.get('text') or '')
        source = (f.get('source') or '').strip()
        confidence = float(f.get('confidence') or 0.0)

        # fix mojibake heuristically for fields missing characters
        if domain == '' and source:
            low = source.lower()
            for k, v in source_domain_map.items():
                if k in low:
                    domain = v
                    break

        reason = None
        if allowed_domains is not None and domain not in allowed_domains:
            reason = 'bad_domain'
        elif confidence < args.min_confidence:
            reason = 'low_conf'
        elif not source:
            reason = 'bad_source'
        elif not text or len(text) < 5:
            reason = 'too_short'
        elif len(text) > args.max_text_len:
            reason = 'too_long'

        key = (domain, text)
        # dedupe policy: if strict, require exact key match; otherwise allow near-match behaviour (current behavior)
        if args.dedupe_strict:
            if key in existing or key in inrun:
                reason = 'near_duplicate'
        else:
            if key in existing or key in inrun:
                reason = 'near_duplicate'

        rec_ts = time.strftime('%Y-%m-%dT%H:%M:%S%z')
        if reason is None:
            # accept
            out = {
                'ts': rec_ts,
                'domain': domain,
                'text': text,
                'source': source,
                'confidence': confidence,
                'accepted': True
            }
            append_jsonl(HARVESTED_PATH, out)
            inrun.add(key)
            accepted.append(out)
            counts[domain] += 1
        else:
            out = {
                'ts': rec_ts,
                'domain': domain,
                'text': text,
                'source': source,
                'confidence': confidence,
                'accepted': False,
                'reason': reason
            }
            append_jsonl(REVIEW_PATH, out)
            rejected.append(out)

    # update progress file
    # Build a more detailed progress document
    progress = {}
    try:
        progress['counts'] = {k: v for k, v in counts.items()}
        # per-reason counts
        reason_counts = defaultdict(int)
        for r in rejected:
            reason_counts[r.get('reason') or 'unknown'] += 1
        progress['reason_counts'] = dict(reason_counts)
        # top sources from accepted
        src_counts = defaultdict(int)
        for a in accepted:
            src_counts[a.get('source') or 'unknown'] += 1
        progress['top_sources'] = dict(sorted(src_counts.items(), key=lambda kv: kv[1], reverse=True)[:10])
    except Exception:
        pass

    progress['ts'] = time.strftime('%Y-%m-%dT%H:%M:%S%z')
    progress['domains'] = {}  # legacy field kept empty; detailed counts provided in 'counts'
    progress['accepted_last'] = len(accepted)
    progress['rejected_last'] = len(rejected)
    progress['proposed_last'] = len(candidates)

    try:
        with open(PROGRESS_PATH, 'w', encoding='utf-8') as fh:
            json.dump(progress, fh, ensure_ascii=False, indent=2)
    except Exception:
        pass

    # print short summary
    print('Postprocess summary: proposed=%d accepted=%d rejected=%d' % (len(candidates), len(accepted), len(rejected)))
    if accepted:
        src_counts = defaultdict(int)
        for a in accepted:
            src_counts[a.get('source') or 'unknown'] += 1
        print('Top sources (accepted):')
        for s,c in sorted(src_counts.items(), key=lambda kv: kv[1], reverse=True)[:5]:
            print('  %s: %d' % (s, c))

    return 0

if __name__ == '__main__':
    sys.exit(main())
