"""Auto-learning loop that fetches missing facts from external providers and integrates them.

Purpose:
- Identify knowledge gaps by asking GK about seed questions or domain topics.
- When GK lacks evidence, call External_InfoProvider (if enabled) to fetch facts.
- Use `nlp` (LLM) to naturalize and summarize facts into short, vetted statements.
- Update GK via `update_knowledge` and log all actions to `artifacts/auto_learn_log.jsonl`.

Safety:
- This script runs in dry-run by default. To perform writes, pass --commit.
- All provider responses are logged but not printed to stdout when commit is enabled.

Usage:
    py -3 scripts/auto_learn_from_providers.py --topics-file configs/auto_learn_topics.txt --commit

"""
from typing import List, Dict, Any
# === AGL auto-injected knobs (idempotent) ===
try:
    import os
    def _to_int(name, default):
        try:
            return int(os.environ.get(name, str(default)))
        except Exception:
            return default
except Exception:
    def _to_int(name, default): return default
_AGL_PREVIEW_1000 = _to_int('AGL_PREVIEW_1000', 1000)

try:
    import os
    def _to_int(name, default):
        try:
            return int(os.environ.get(name, str(default)))
        except Exception:
            return default
except Exception:
    def _to_int(name, default): return default
import argparse
import os
import json
import time
ROOT = os.path.dirname(os.path.dirname(__file__))
ARTIFACTS = os.path.join(ROOT, 'artifacts')
LOG_PATH = os.path.join(ARTIFACTS, 'auto_learn_log.jsonl')
try:
    from Integration_Layer.Domain_Router import get_engine
except Exception:
    get_engine = None
def load_topics(path: str) -> List[str]:
    if not path or not os.path.exists(path):
        return ['urban traffic congestion causes', 'public transit demand management', 'traffic calming strategies', 'ecosystem-inspired routing']
    out = []
    with open(path, 'r', encoding='utf-8') as fh:
        for ln in fh:
            s = ln.strip()
            if s:
                out.append(s)
    return out
def log(obj: Dict[str, Any]):
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, 'a', encoding='utf-8') as lf:
            lf.write(json.dumps(obj, ensure_ascii=False) + '\n')
    except Exception:
        pass
def main(args):
    topics = load_topics(args.topics_file)
    dry = not args.commit
    if get_engine is None:
        print('Domain router not available; aborting.')
        return
    gk = get_engine('knowledge')
    nlp = None
    try:
        nlp = get_engine('nlp')
    except Exception:
        nlp = None
    for t in topics:
        ts = int(time.time())
        q = t
        try:
            gk_out = gk.ask(q, context=[f'auto_learn:seed'])
        except Exception as e:
            gk_out = {'ok': False, 'error': str(e), 'text': ''}
        entry = {'ts': ts, 'topic': t, 'gk_ok': bool(gk_out.get('ok')), 'gk_text': gk_out.get('text') if isinstance(gk_out, dict) else str(gk_out)}
        no_info = False
        if not gk_out or (isinstance(gk_out, dict) and (not gk_out.get('text'))):
            no_info = True
        if no_info:
            try:
                prov_ctx = [f'auto_learn:fetch', 'topic:{t}']
                prov_out = gk.ask(q, context=prov_ctx)
                entry['provider'] = {'ok': bool(prov_out.get('ok')), 'text_preview': (prov_out.get('text') or '')[:800]}
            except Exception as e:
                entry['provider'] = {'ok': False, 'error': str(e)}
            nat = None
            try:
                if nlp and hasattr(nlp, 'naturalize_answer'):
                    facts = []
                    if prov_out and isinstance(prov_out, dict) and prov_out.get('text'):
                        facts = [{'object': prov_out.get('text'), 'source': prov_out.get('engine') or 'provider', 'confidence': 0.8}]
                    nat = nlp.naturalize_answer(facts, q, provider_answer=prov_out.get('text') if isinstance(prov_out, dict) else None)
                    entry['naturalized_preview'] = (nat.get('text') if isinstance(nat, dict) else str(nat))[:_AGL_PREVIEW_1000]
            except Exception as e:
                entry['naturalize_error'] = str(e)
            if not dry:
                try:
                    to_insert = []
                    if prov_out and isinstance(prov_out, dict) and prov_out.get('text'):
                        to_insert.append({'subject': q, 'predicate': 'fact', 'object': prov_out.get('text'), 'source': prov_out.get('engine')})
                    if to_insert:
                        upd = gk.update_knowledge(to_insert)
                        entry['update_result'] = upd
                except Exception as e:
                    entry['update_error'] = str(e)
        log(entry)
        print('.', end='', flush=True)
    print('\nDone. Logs saved to', LOG_PATH)
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--topics-file', default='configs/auto_learn_topics.txt')
    p.add_argument('--commit', action='store_true', help='Apply knowledge updates (default: dry-run)')
    ns = p.parse_args()
    main(ns)
