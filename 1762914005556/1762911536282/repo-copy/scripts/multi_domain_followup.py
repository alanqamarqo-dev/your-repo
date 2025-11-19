# -*- coding: utf-8 -*-
"""
Follow-up detailed prompt: ask the system for a 6-step implementation plan with cost, social acceptance, environmental metrics,
and then score it using the same heuristics as multi_domain_ag_test.py.
"""
from __future__ import annotations
import json
import os
import re
from pathlib import Path
from typing import Dict, Any

PROMPT = (
    "أعد إجابة موسعة ومنفّذة حول: 'صمم حلًا مبتكرًا لمشكلة ازدحام المرور في مدينة كبرى', "
    "اطرح خطة مفصّلة مكوّنة من 6 خطوات قابلة للتطبيق، وكل خطوة تضم: وصفًا تقنيًا، تقديرًا تكاليفيًا تقريبيًا (نطاق تكلفة منخفض-عالي)، "
    "مؤشرات أداء قابلة للقياس (KPIs)، تحليلًا للآثار الاجتماعية (قبول، توزيع المنافع)، تحليلاً بيئيًا (انبعاثات، استدامة)، وخطة تواصل/تبنٍّ مجتمعي. "
    "استند إلى أمثلة من الطبيعة عند الاقتضاء واذكر أي افتراضات رقمية تفصيلية تفيد التقديرات. أجب بالعربية مع ملاحظات تقنية باللغة الإنجليزية إذا لزم الأمر."
)

KEYWORDS = {
    'creativity': ['جديد', 'مبتكر', 'ابتكار', 'أصالة', 'حل غير تقليدي'],
    'scientific': ['مستوحى من', 'نظام طبيعي', 'مستعمرات النمل', 'أسراب', 'محاكاة', 'معادلة', 'model', 'data'],
    'social': ['القبول', 'مجتمعي', 'عدالة', 'مشاركة', 'stakeholders'],
    'economic': ['تكلفة', 'تمويل', 'ROI', 'عوائد', 'cost', 'budget'],
    'environmental': ['انبعاثات', 'كربون', 'استدامة', 'habitat', 'sustainable']
}
NUM_RE = re.compile(r"\b\d+[\d.,]*\b")


def call_provider():
    try:
        from Core_Engines.External_InfoProvider import ExternalInfoProvider
    except Exception as e:
        return {'ok': False, 'error': f'import_failed: {e}'}
    try:
        prov = ExternalInfoProvider()
    except Exception as e:
        return {'ok': False, 'error': f'init_failed: {e}'}
    try:
        res = prov.fetch_facts(PROMPT, hints=['implementation', 'policy', 'costing'])
    except Exception as e:
        return {'ok': False, 'error': f'fetch_failed: {e}'}
    return res


def score_answer(text: str) -> Dict[str, Any]:
    low = (text or '').lower()
    scores = {}
    # creativity
    c_hits = sum(1 for k in KEYWORDS['creativity'] if k in low)
    scores['creativity'] = min(25, int((c_hits / max(1, len(KEYWORDS['creativity']))) * 25))
    # scientific
    s_hits = sum(1 for k in KEYWORDS['scientific'] if k in low)
    s_num = 1 if NUM_RE.search(text) else 0
    s_causal = 1 if 'لأن' in low or 'بسبب' in low else 0
    scores['scientific'] = min(25, int(((s_hits + s_num + s_causal) / (len(KEYWORDS['scientific'])/4 + 2)) * 25))
    # social
    so_hits = sum(1 for k in KEYWORDS['social'] if k in low)
    so_impl = 1 if 'خطة' in low or 'مراحل' in low or 'تواصل' in low else 0
    scores['social'] = min(20, int(((so_hits + so_impl) / (len(KEYWORDS['social'])/3 + 1)) * 20))
    # economic
    e_hits = sum(1 for k in KEYWORDS['economic'] if k in low)
    e_num = 1 if NUM_RE.search(text) else 0
    scores['economic'] = min(15, int(((e_hits + e_num) / (len(KEYWORDS['economic'])/3 + 1)) * 15))
    # environmental
    env_hits = sum(1 for k in KEYWORDS['environmental'] if k in low)
    scores['environmental'] = min(15, int((env_hits / max(1, len(KEYWORDS['environmental']))) * 15))
    # bonus for explicit KPIs and cost bands
    bonus = 0
    if 'kpi' in low or 'مؤشر' in low:
        bonus += 2
    if 'تكلفة' in low and NUM_RE.search(text):
        bonus += 3
    scores['bonus'] = bonus
    return scores


def main():
    print('Asking provider for a detailed 6-step implementation plan...')
    res = call_provider()
    Path('artifacts/reports').mkdir(parents=True, exist_ok=True)
    outp = Path('artifacts/reports/multi_domain_followup.json')
    if not res.get('ok'):
        print('Provider failed:', res.get('error'))
        with outp.open('w', encoding='utf-8') as fh:
            json.dump({'ok': False, 'error': res.get('error')}, fh, ensure_ascii=False, indent=2)
        return
    answer = res.get('answer') or ''
    print('\n--- Provider detailed answer ---\n')
    print(answer)
    scores = score_answer(answer)
    final = sum(scores.get(k,0) for k in ['creativity','scientific','social','economic','environmental']) + scores.get('bonus',0)
    pct = (final/100.0)*100.0
    report = {'answer': answer, 'scores': scores, 'final_percentage': pct}
    with outp.open('w', encoding='utf-8') as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    print('\nScores:')
    for k,v in scores.items():
        print(f' - {k}: {v}')
    print(f'Final heuristic AGI percentage: {pct:.1f}%')
    print('Report saved to', str(outp))

if __name__ == "__main__":
    main()
