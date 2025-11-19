# -*- coding: utf-8 -*-
"""
Multi-domain AGI competency test: single comprehensive question and rubric-based scoring.
Usage:
  $env:PYTHONPATH='D:\\AGL'; .venv\\Scripts\\python.exe scripts\\multi_domain_ag_test.py --live

The script will attempt to call Core_Engines.External_InfoProvider in live mode and use the provider's
"answer" field as the system response. It then evaluates that response across 5 domains with
heuristic keyword/feature matching (as requested). Results are saved to artifacts/reports/multi_domain_ag_test.json
"""
from __future__ import annotations
import argparse
import json
import os
import re
from pathlib import Path
from typing import Dict, List

QUESTION = (
    "صمم حلًا مبتكرًا لمشكلة ازدحام المرور في مدينة كبرى، "
    "مع شرح التأثيرات الاجتماعية والاقتصادية والبيئية، مستخدمًا أمثلة من أنظمة طبيعية للإلهام."
)

# Domain weights / max points
DOMAIN_MAX = {
    'creativity': 25,
    'scientific': 25,
    'social': 20,
    'economic': 15,
    'environmental': 15,
}

# Keywords / signals per domain (Arabic + English tokens)
KEYWORDS = {
    'creativity': ['جديد', 'مبتكر', 'ابتكار', 'أصالة', 'فكرة جديدة', 'حل غير تقليدي', 'تفكير جانبي', 'novel', 'innovative'],
    'scientific': ['مستوحى من', 'نظام طبيعي', 'مستعمرات النمل', 'أنهار', 'شبكات', 'محاكاة', 'محاكاة حيوية', 'طاقة', 'معادلة', 'quantitative', 'data', 'model'],
    'social': ['القبول', 'مجتمعي', 'عدالة', 'توزيع', 'سكان', 'تأثير اجتماعي', 'equity', 'acceptance', 'community'],
    'economic': ['تكلفة', 'تكلفة منخفضة', 'تكلفة-فائدة', 'الاستثمار', 'عوائد', 'benefit', 'جدوى', 'تمويل', 'cost', 'ROI'],
    'environmental': ['استدامة', 'بصمة كربونية', 'انبعاثات', 'بيئي', 'تناغم', 'habitat', 'sustainable', 'low-carbon']
}

# Extra signals: presence of numbers (quant analysis), causal words, implementation steps

NUM_RE = re.compile(r"\b\d+[\d.,]*\b")
CAUSAL_WORDS = ['لأن', 'بسبب', 'مما يؤدي', 'نتيجة', 'because', 'therefore', 'hence']
IMPLEMENT_WORDS = ['نفّذ', 'تنفيذ', 'تطبيق', 'خطة', 'مراحل', 'steps', 'implement']


def call_provider_live(prompt: str, model: str | None = None):
    try:
        from Core_Engines.External_InfoProvider import ExternalInfoProvider
    except Exception as e:
        return {'ok': False, 'error': f'import_failed: {e}'}

    try:
        prov = ExternalInfoProvider(model=model)
    except Exception as e:
        return {'ok': False, 'error': f'init_failed: {e}'}

    q = f"{prompt}\n\nPlease answer in Arabic (or Arabic+English). Provide a clear solution and explain social, economic, environmental effects."
    try:
        res = prov.fetch_facts(q, hints=['multi-domain', 'policy', 'design'])
    except Exception as e:
        return {'ok': False, 'error': f'fetch_failed: {e}'}

    if not res.get('ok'):
        return {'ok': False, 'error': res.get('error')}

    return {'ok': True, 'answer': res.get('answer'), 'facts': res.get('facts', [])}


def score_text(answer: str) -> Dict[str, int]:
    text = answer or ''
    low = text.lower()
    scores: Dict[str, int] = {}

    # Creativity: match keywords + evidence of novelty phrase
    c_hits = sum(1 for k in KEYWORDS['creativity'] if k in low)
    creativity = min(DOMAIN_MAX['creativity'], int((c_hits / max(1, len(KEYWORDS['creativity']))) * DOMAIN_MAX['creativity']))

    # Scientific: match nature-inspired mentions, presence of causal explanation and numbers/models
    s_hits = sum(1 for k in KEYWORDS['scientific'] if k in low)
    s_num = 1 if NUM_RE.search(text) else 0
    s_causal = 1 if any(w in low for w in CAUSAL_WORDS) else 0
    scientific = min(DOMAIN_MAX['scientific'], int(((s_hits + s_num + s_causal) / (len(KEYWORDS['scientific'])/4 + 2)) * DOMAIN_MAX['scientific']))

    # Social: mentions of acceptance, equity, distribution; mention of stakeholders
    so_hits = sum(1 for k in KEYWORDS['social'] if k in low)
    so_impl = 1 if any(w in low for w in IMPLEMENT_WORDS) else 0
    social = min(DOMAIN_MAX['social'], int(((so_hits + so_impl) / (len(KEYWORDS['social'])/3 + 1)) * DOMAIN_MAX['social']))

    # Economic: cost/benefit keywords, ROI, funding
    e_hits = sum(1 for k in KEYWORDS['economic'] if k in low)
    e_num = 1 if NUM_RE.search(text) else 0
    economic = min(DOMAIN_MAX['economic'], int(((e_hits + e_num) / (len(KEYWORDS['economic'])/3 + 1)) * DOMAIN_MAX['economic']))

    # Environmental: sustainability, carbon, habitat
    env_hits = sum(1 for k in KEYWORDS['environmental'] if k in low)
    env = min(DOMAIN_MAX['environmental'], int((env_hits / max(1, len(KEYWORDS['environmental'])) ) * DOMAIN_MAX['environmental']))

    # Slight bonus if implementation steps and causal logic exist
    bonus = 0
    if any(w in low for w in IMPLEMENT_WORDS) and any(w in low for w in CAUSAL_WORDS):
        bonus = 2

    scores['creativity'] = creativity
    scores['scientific'] = scientific
    scores['social'] = social
    scores['economic'] = economic
    scores['environmental'] = env
    scores['bonus'] = bonus
    return scores


def compute_final_percentage(scores: Dict[str, int]) -> float:
    total = 0.0
    for k, maxp in DOMAIN_MAX.items():
        total += scores.get(k, 0)
    total += scores.get('bonus', 0)
    # normalize to 100 (domain max sums to 100)
    pct = (total / 100.0) * 100.0
    return pct


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--live', action='store_true', help='Use live ExternalInfoProvider')
    parser.add_argument('--model', type=str, default=None, help='Optional model override')
    args = parser.parse_args()

    use_live = args.live or os.getenv('AGL_EXTERNAL_INFO_ENABLED', '0') == '1'

    print('Running Multi-domain AGI competency test')
    print('Question:')
    print(QUESTION)
    print()

    provider_result = None
    if use_live:
        print('[info] Calling live ExternalInfoProvider...')
        provider_result = call_provider_live(QUESTION, model=args.model)
        if not provider_result.get('ok'):
            print('[warn] provider failed:', provider_result.get('error'))

    if provider_result and provider_result.get('ok'):
        answer = provider_result.get('answer') or ''
    else:
        # fallback: simple echo and heuristic (we do not craft answers)
        print('[info] No live answer available; using fallback placeholder (system offline).')
        answer = 'لا يوجد رد حي؛ النظام في وضع التجربة.'

    print('\n=== System answer ===')
    print(answer)

    scores = score_text(answer)
    final_pct = compute_final_percentage(scores)

    report = {
        'question': QUESTION,
        'answer': answer,
        'scores': scores,
        'final_percentage': final_pct,
    }

    outp = Path('artifacts/reports/multi_domain_ag_test.json')
    outp.parent.mkdir(parents=True, exist_ok=True)
    with outp.open('w', encoding='utf-8') as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)

    print('\nScores:')
    for k, v in scores.items():
        print(f' - {k}: {v}/{DOMAIN_MAX.get(k, v)}')
    print(f'\nFinal AGI percentage (heuristic): {final_pct:.1f}%')
    print('\nReport saved to:', str(outp))


if __name__ == '__main__':
    main()
