import os
import sys
import json
import time
import random
import hashlib
import pathlib
from datetime import datetime, timezone

# ensure repo root on path
sys.path.append(os.getcwd())

import yaml

from Core_Engines.External_InfoProvider import ExternalInfoProvider
from Core_Engines.General_Knowledge import GeneralKnowledgeEngine
# optional adaptive memory hints
try:
    from infra.adaptive.AdaptiveMemory import suggest_harvest_hints
except Exception:
    suggest_harvest_hints = None

PLAN_PATH = os.getenv('AGL_HARVEST_PLAN', 'configs/harvest_plan.yaml')
STATE_PATH = os.getenv('AGL_HARVEST_STATE', 'artifacts/harvest_state.json')
FACTS_LOG = os.getenv('AGL_HARVEST_LOG', 'artifacts/harvested_facts.jsonl')

MIN_CONF = float(os.getenv('AGL_HARVEST_MIN_CONF', '0.70'))


def load_yaml(p):
    p = pathlib.Path(p)
    if not p.exists():
        raise FileNotFoundError(p)
    with p.open('r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_state():
    p = pathlib.Path(STATE_PATH)
    if not p.exists():
        return {'progress': {}, 'last_run': None}
    try:
        return json.loads(p.read_text(encoding='utf-8'))
    except Exception:
        return {'progress': {}, 'last_run': None}


def save_state(state: dict):
    p = pathlib.Path(STATE_PATH)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')


def append_log(rec: dict):
    p = pathlib.Path(FACTS_LOG)
    p.parent.mkdir(parents=True, exist_ok=True)
    # write using utf-8-sig when file is newly created so PowerShell shows Arabic correctly
    write_mode = 'a'
    encoding = 'utf-8'
    if not p.exists():
        # initial write with BOM
        encoding = 'utf-8-sig'
    with p.open(write_mode, encoding=encoding) as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def hash_text(t: str) -> str:
    return hashlib.sha256((t or '').strip().encode('utf-8')).hexdigest()


def pick_domain(plan: dict, state: dict) -> dict | None:
    for d in plan.get('domains', []):
        name = d['name']
        cur = int(state.get('progress', {}).get(name, 0))
        if cur < int(d.get('target_facts', 50)):
            return d
    return None


def pick_prompt(domain: dict) -> str:
    seeds = domain.get('seeds', [])
    if not seeds:
        return f"زودني بحقائق موثقة حول مجال {domain['name']}."
    seed = random.choice(seeds)
    return f"استخرج حقائق دقيقة وموثقة حول «{seed}» ضمن مجال {domain['name']}."


def main():
    enabled = os.getenv('AGL_EXTERNAL_INFO_ENABLED', '0') == '1' or os.getenv('EXTERNAL_INFO_ENABLED', '0') == '1'
    if not enabled:
        print('[harvester] external provider disabled; exit.')
        return

    plan = load_yaml(PLAN_PATH)
    state = load_state()

    gk = GeneralKnowledgeEngine()
    # Allow pluggable external info implementation. If AGL_EXTERNAL_INFO_IMPL=openai_engine
    # use the OpenAIAdapter which wraps Core_Engines.OpenAI_KnowledgeEngine. Otherwise default
    # to the existing ExternalInfoProvider implementation.
    impl = os.getenv('AGL_EXTERNAL_INFO_IMPL', '').lower()
    if impl in ('openai_engine', 'openai_adapter'):
        try:
            from Core_Engines.OpenAI_Adapter import OpenAIAdapter
            ext = OpenAIAdapter(model=os.getenv('AGL_EXTERNAL_INFO_MODEL', None))
        except Exception:
            # fallback to ExternalInfoProvider if adapter missing or fails
            ext = ExternalInfoProvider(model=os.getenv('AGL_EXTERNAL_INFO_MODEL', None))
    elif impl in ('ollama_engine', 'ollama_adapter'):
        try:
            from Core_Engines.Ollama_Adapter import OllamaAdapter
            ext = OllamaAdapter(model=os.getenv('AGL_EXTERNAL_INFO_MODEL', None))
        except Exception:
            ext = ExternalInfoProvider(model=os.getenv('AGL_EXTERNAL_INFO_MODEL', None))
    else:
        ext = ExternalInfoProvider(model=os.getenv('AGL_EXTERNAL_INFO_MODEL', None))

    domain = pick_domain(plan, state)
    if not domain:
        print('[harvester] all domains reached targets; exit.')
        return
    # normalize domain name to avoid accidental double-dots like 'physics..classical'
    domain_name = (domain.get('name') or '').replace('..', '.')

    q = pick_prompt(domain)
    hints = [domain['name']]
    # append adaptive hints if available (best-effort, non-breaking)
    if suggest_harvest_hints is not None:
        try:
            hints = hints + suggest_harvest_hints(max_items=8)
        except Exception:
            pass

    res = ext.fetch_facts(q, hints=hints)
    if not res.get('ok'):
        print('[harvester] fetch failed:', res.get('error'))
        return

    facts = res.get('facts', [])
    if not facts:
        print('[harvester] no facts returned.')
        return

    accepted = []
    for f in facts:
        txt = (f.get('text') or '').strip()
        src = f.get('source') or ''
        conf = float(f.get('confidence') or 0.0)
        if not txt or conf < max(MIN_CONF, float(plan.get('policy', {}).get('min_confidence', 0.7))):
            continue
        if plan.get('policy', {}).get('require_source', True) and not src:
            continue
        hid = hash_text(txt)
        # normalize domain on each fact too
        accepted.append({'id': hid, 'text': txt, 'source': src, 'confidence': conf, 'domain': domain_name})

    if not accepted:
        print('[harvester] nothing passed prefilter.')
        return

    # Enforce target caps: don't accept more facts than the domain target
    name = domain.get('name')
    try:
        target = int(domain.get('target_facts', 50))
    except Exception:
        target = 50
    cur = int(state.get('progress', {}).get(name, 0))
    remaining = max(0, target - cur)
    if remaining <= 0:
        print(f"[harvester] domain {name} has already reached target ({cur}/{target}); skipping.")
        return
    if len(accepted) > remaining:
        # trim to remaining to avoid overshooting the target
        accepted = accepted[:remaining]
        print(f"[harvester] trimmed accepted facts to remaining={remaining} for domain={name} to avoid overshoot")

    # upsert into GK graph; transform to expected shape
    to_upsert = []
    ts = datetime.now(timezone.utc).isoformat()
    for a in accepted:
        to_upsert.append({
            'subject': a['domain'],
            'predicate': 'fact',
            'object': a['text'],
            'confidence': a['confidence'],
            'source': a['source'],
            'added_by': f"external_info_provider:{os.getenv('AGL_EXTERNAL_INFO_MODEL', 'gpt-4o-mini')}",
            'added_at': ts
        })

    # detect conflicts vs existing graph: if same subject+predicate but different object
    safe_upsert = []
    review_items = []
    try:
        existing = getattr(gk.graph, 'edges', [])
    except Exception:
        existing = []

    def has_conflict(subject, predicate, obj):
        for (s, p, o, w) in existing:
            if s == subject and p == predicate and o != obj:
                return True, o
        return False, None

    for item in to_upsert:
        subj = item.get('subject')
        pred = item.get('predicate')
        obj = item.get('object')
        conflict, existing_obj = has_conflict(subj, pred, obj)
        if conflict:
            # push to review queue
            review_items.append({
                'ts': ts,
                'subject': subj,
                'predicate': pred,
                'object': obj,
                'source': item.get('source'),
                'confidence': item.get('confidence'),
                'existing_object': existing_obj,
                'added_by': item.get('added_by')
            })
        else:
            safe_upsert.append(item)

    # upsert safe items
    try:
        if safe_upsert:
            gk.update_knowledge(safe_upsert)
    except Exception as e:
        print('[harvester] update_knowledge failed:', str(e))

    # write review items to artifacts/harvest_review.jsonl
    if review_items:
        review_path = pathlib.Path('artifacts/harvest_review.jsonl')
        review_path.parent.mkdir(parents=True, exist_ok=True)
        with review_path.open('a', encoding='utf-8') as rf:
            for r in review_items:
                rf.write(json.dumps(r, ensure_ascii=False) + '\n')

    for a in accepted:
        append_log({
            'ts': ts,
            'domain': a['domain'],
            'text': a['text'],
            'source': a['source'],
            'confidence': a['confidence']
        })

    # Persist per-fact cache files (help retriever/indexing)
    try:
        cache_dir = pathlib.Path('artifacts/external_info_cache')
        cache_dir.mkdir(parents=True, exist_ok=True)
        for a in accepted:
            fid = a.get('id') or hash_text(a.get('text'))
            cache_path = cache_dir / f"{fid}.json"
            payload = {
                'answer': None,
                'facts': [
                    {
                        'id': fid,
                        'text': a.get('text'),
                        'source': a.get('source'),
                        'confidence': a.get('confidence'),
                        'domain': a.get('domain')
                    }
                ],
                'origin': 'harvester',
                'added_at': ts
            }
            # write using utf-8-sig to help Windows PowerShell display
            try:
                with cache_path.open('w', encoding='utf-8-sig') as cf:
                    cf.write(json.dumps(payload, ensure_ascii=False, indent=2))
            except Exception:
                # best-effort: fallback to utf-8 without BOM
                with cache_path.open('w', encoding='utf-8') as cf:
                    cf.write(json.dumps(payload, ensure_ascii=False, indent=2))
    except Exception as e:
        print('[harvester] warning: failed to write per-fact cache:', str(e))

    # update state
    name = domain['name']
    state['progress'][name] = int(state.get('progress', {}).get(name, 0)) + len(accepted)
    state['last_run'] = ts
    save_state(state)

    print(f"[harvester] accepted={len(accepted)} domain={name} progress={state['progress'][name]}/{domain.get('target_facts')}")


if __name__ == '__main__':
    main()
