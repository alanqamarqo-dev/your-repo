"""Supervisor helper for routing harvested facts to protection and learning units.

This is a light-weight script intended to run inside the container or locally for tests.
"""
import json
import pathlib
from typing import List

ARTIFACTS = pathlib.Path('artifacts')
FACTS_LOG = ARTIFACTS / 'harvested_facts.jsonl'
PROTECTED_STORE = ARTIFACTS / 'protected'  # harmful infos
LEARNING_STORE = ARTIFACTS / 'for_learning'  # safe facts for learning


def classify_fact(rec: dict) -> str:
    """Very small placeholder classifier: if 'harm' or 'attack' in text -> harmful."""
    txt = (rec.get('text') or '').lower()
    if any(k in txt for k in ('harm', 'attack', 'poison', 'explosive')):
        return 'harmful'
    return 'safe'


def route_facts(last_n: int = 100):
    PROTECTED_STORE.mkdir(parents=True, exist_ok=True)
    LEARNING_STORE.mkdir(parents=True, exist_ok=True)
    if not FACTS_LOG.exists():
        print('No harvested facts yet')
        return
    with FACTS_LOG.open('r', encoding='utf-8') as fh:
        lines = fh.read().splitlines()
    recent = lines[-last_n:]
    for l in recent:
        try:
            rec = json.loads(l)
        except Exception:
            continue
        c = classify_fact(rec)
        if c == 'harmful':
            outp = PROTECTED_STORE / (rec.get('id') or 'unknown')
            outp.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding='utf-8')
        else:
            outp = LEARNING_STORE / (rec.get('id') or 'unknown')
            outp.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Routed {len(recent)} facts (protected -> {PROTECTED_STORE}, learning -> {LEARNING_STORE})')


if __name__ == '__main__':
    route_facts()
