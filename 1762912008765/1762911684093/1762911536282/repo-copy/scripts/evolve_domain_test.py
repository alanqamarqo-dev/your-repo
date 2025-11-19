# -*- coding: utf-8 -*-
"""
Evolve-domain test harness

Runs iterative cycles where we:
 - fetch external facts for a novel domain (ExternalInfoProvider)
 - ingest accepted facts into GeneralKnowledgeEngine
 - ask a set of diagnostic questions before/after ingestion
 - measure simple improvement metrics (answer length, keyword hits, 'no_evidence' sentinel)

Usage (PowerShell):
  $env:PYTHONPATH='D:\\AGL'; .venv\\Scripts\\python.exe .\\scripts\\evolve_domain_test.py --domain "self-healing metamaterials" --iterations 3 # type: ignore

The script defaults to mock provider unless --live is passed.
"""
from __future__ import annotations
import argparse
import json
import os
import re
from pathlib import Path
from typing import List, Dict, Any

OUT_DIR = Path('artifacts/reports')
OUT_DIR.mkdir(parents=True, exist_ok=True)

NUM_RE = re.compile(r"\b\d+[\d.,]*\b")


def call_provider_for_domain(domain: str, live: bool) -> Dict[str, Any]:
    if not live:
        os.environ['AGL_EXTERNAL_INFO_MOCK'] = '1'
    try:
        from Core_Engines.External_InfoProvider import ExternalInfoProvider
    except Exception as e:
        return {'ok': False, 'error': f'import_failed: {e}'}
    try:
        prov = ExternalInfoProvider()
    except Exception as e:
        return {'ok': False, 'error': f'init_failed: {e}'}
    try:
        prompt = f"اجمع حقائق ومراجع وموجز عن المجال التالي بصيغة مفيدة للمعرفة: {domain}"
        res = prov.fetch_facts(prompt, hints=[domain, 'overview', 'definitions'])
    except Exception as e:
        return {'ok': False, 'error': f'fetch_failed: {e}'}
    return res


def ingest_into_gk(facts: List[Dict[str, Any]], domain: str) -> Dict[str, Any]:
    try:
        from Core_Engines.General_Knowledge import GeneralKnowledgeEngine
    except Exception as e:
        return {'ok': False, 'error': f'import_gk_failed: {e}'}
    try:
        gke = GeneralKnowledgeEngine()
    except Exception as e:
        return {'ok': False, 'error': f'gk_init_failed: {e}'}

    accepted = []
    for f in (facts or []):
        # standardize fact representation
        if isinstance(f, dict):
            txt = f.get('text') or f.get('object') or ''
            src = f.get('source') or f.get('domain') or 'external'
            try:
                conf = float(f.get('confidence') or 0.5)
            except Exception:
                conf = 0.5
            accepted.append({'subject': domain[:200], 'predicate': 'fact', 'object': txt, 'source': src, 'confidence': conf})
        elif isinstance(f, (list, tuple)) and len(f) >= 2:
            accepted.append({'subject': domain[:200], 'predicate': 'fact', 'object': f[1], 'source': f[0], 'confidence': 0.5})
        else:
            accepted.append({'subject': domain[:200], 'predicate': 'fact', 'object': str(f), 'source': 'external', 'confidence': 0.5})

    try:
        res = gke.update_knowledge(accepted)
        return {'ok': True, 'accepted_count': len(accepted), 'detail': res}
    except Exception as e:
        return {'ok': False, 'error': f'update_failed: {e}'}


def ask_questions(domain: str, questions: List[str]) -> List[Dict[str, Any]]:
    try:
        from Core_Engines.General_Knowledge import GeneralKnowledgeEngine
        gke = GeneralKnowledgeEngine()
    except Exception as e:
        return [{'ok': False, 'error': f'gk_missing: {e}'}]

    results = []
    for q in questions:
        try:
            ans = gke.ask(q, context=[domain])
            # normalize
            text = ans.get('text') if isinstance(ans, dict) else str(ans)
            results.append({'question': q, 'answer': text or '', 'ok': True})
        except Exception as e:
            results.append({'question': q, 'answer': '', 'ok': False, 'error': str(e)})
    return results


def score_answer(answer: str, domain_keywords: List[str]) -> Dict[str, Any]:
    low = (answer or '').lower()
    length = len(answer.split())
    kw_hits = sum(1 for k in domain_keywords if k.lower() in low)
    num_found = 1 if NUM_RE.search(answer) else 0
    no_evidence = 1 if 'no_evidence' in low or 'لم أجد' in low else 0
    score = max(0, (kw_hits * 2) + min(10, length//20) + (num_found * 2) - (no_evidence * 10))
    return {'length_words': length, 'keyword_hits': kw_hits, 'numeric_present': bool(num_found), 'no_evidence': bool(no_evidence), 'score': score}


def slugify(s: str) -> str:
    return re.sub(r'[^a-z0-9]+', '_', s.lower())[:60]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--domain', required=False, default='self-healing metamaterials', help='Novel domain to evolve in')
    parser.add_argument('--iterations', type=int, default=3)
    parser.add_argument('--live', action='store_true', help='Use live provider if set')
    args = parser.parse_args()

    domain = args.domain
    iterations = args.iterations
    live = args.live

    print(f'Running evolution test for domain: "{domain}" iterations={iterations} live={live}')

    # define diagnostic questions (simple but targeted)
    questions = [
        f'ما هو تعريف {domain}؟',
        f'ما التطبيقات العملية لـ {domain}؟',
        f'اذكر ثلاثة مراجع أو مواضيع ذات علاقة بـ {domain}.'
    ]

    # build domain keyword set from domain words
    domain_keywords = [w for w in re.split(r'\W+', domain) if w]

    slug = slugify(domain)
    outp = OUT_DIR / f'evolve_{slug}.json'

    # baseline: ask before ingestion
    baseline_answers = ask_questions(domain, questions)
    baseline_scores = [score_answer(a.get('answer',''), domain_keywords) for a in baseline_answers]

    report = {'domain': domain, 'iterations': [] , 'baseline': {'answers': baseline_answers, 'scores': baseline_scores}}

    for it in range(1, iterations + 1):
        print(f'Iteration {it}: fetching facts...')
        prov = call_provider_for_domain(domain, live)
        facts = prov.get('facts') or []
        # ingest
        print(f'Iteration {it}: ingesting {len(facts)} facts into GK...')
        ingest_res = ingest_into_gk(facts, domain)

        # ask diagnostic questions again
        answers = ask_questions(domain, questions)
        scores = [score_answer(a.get('answer',''), domain_keywords) for a in answers]

        report['iterations'].append({'iteration': it, 'provider': prov, 'ingest': ingest_res, 'answers': answers, 'scores': scores})

        # save intermediate
        with outp.open('w', encoding='utf-8') as fh:
            json.dump(report, fh, ensure_ascii=False, indent=2)

    print('Evolution run complete. Report saved to', str(outp))


if __name__ == '__main__':
    main()
