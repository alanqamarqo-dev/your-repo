# -*- coding: utf-8 -*-
"""
Post-process a provider answer using the SocialInteractionEngine.

Loads `artifacts/reports/multi_domain_followup.json`, runs social analysis,
adds the social cues to the report and recomputes the 'social' score using
the same heuristic used by `multi_domain_followup.py`.

Writes updated report to `artifacts/reports/multi_domain_followup_with_social.json`.
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Dict, Any

REPORT_IN = Path("artifacts/reports/multi_domain_followup.json")
REPORT_OUT = Path("artifacts/reports/multi_domain_followup_with_social.json")

KEYWORDS_SOCIAL = ['القبول', 'مجتمعي', 'عدالة', 'مشاركة', 'stakeholders']
NUM_RE = re.compile(r"\b\d+[\d.,]*\b")


def load_report(path: Path) -> Dict[str, Any]:
    with path.open('r', encoding='utf-8') as fh:
        return json.load(fh)


def try_import_social_engine():
    try:
        from Core_Engines.Social_Interaction import SocialInteractionEngine
    except Exception as e:
        return None, str(e)
    try:
        eng = SocialInteractionEngine()
        return eng, None
    except Exception as e:
        return None, str(e)


def recompute_social_score(text: str, social_cues: Dict[str, Any]) -> int:
    low = (text or '').lower()
    so_hits = sum(1 for k in KEYWORDS_SOCIAL if k in low)
    # treat presence of explicit social cues from engine as additional signal
    cues_count = 0
    if isinstance(social_cues, dict):
        # social_cues may include keys like 'tone','concerns','stakeholders'
        for v in social_cues.values():
            if isinstance(v, (list, tuple)):
                cues_count += len(v)
            elif isinstance(v, str) and len(v.strip()) > 3:
                cues_count += 1
    so_impl = 1 if 'خطة' in low or 'مراحل' in low or 'تواصل' in low else 0
    # combine heuristic similarly to original script but include cues_count
    val = ((so_hits + so_impl + (cues_count/2)) / (len(KEYWORDS_SOCIAL)/3 + 1)) * 20
    score = min(20, int(val))
    return score


def main():
    if not REPORT_IN.exists():
        print('Input report not found:', REPORT_IN)
        return
    report = load_report(REPORT_IN)
    answer = report.get('answer', '')

    eng, err = try_import_social_engine()
    social_analysis = None
    if eng is None:
        social_analysis = {'error': f'failed_import_or_init: {err}'}
        print('Could not import or init SocialInteractionEngine:', err)
    else:
        try:
            social_analysis = eng.analyze_social_cues(answer)
        except Exception as e:
            social_analysis = {'error': f'analysis_failed: {e}'}
            print('Social engine analysis failed:', e)

    # recompute social score
    new_social = recompute_social_score(answer, social_analysis)

    # write extended report
    extended = dict(report)
    extended['social_analysis'] = social_analysis
    if 'scores' not in extended:
        extended['scores'] = {}
    extended['scores']['social_via_engine'] = new_social
    # also keep original social score if present
    orig_social = extended['scores'].get('social', None)
    extended['scores']['social_original'] = orig_social

    # recompute final percentage: replace social with new_social if higher
    used_social = max(new_social, orig_social or 0)
    # compute final as sum of domains with updated social
    creativity = extended['scores'].get('creativity', 0)
    scientific = extended['scores'].get('scientific', 0)
    economic = extended['scores'].get('economic', 0)
    environmental = extended['scores'].get('environmental', 0)
    bonus = extended['scores'].get('bonus', 0)
    final = creativity + scientific + used_social + economic + environmental + bonus
    pct = (final / 100.0) * 100.0
    extended['final_percentage_with_social_engine'] = pct

    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_OUT.open('w', encoding='utf-8') as fh:
        json.dump(extended, fh, ensure_ascii=False, indent=2)

    print('Wrote updated report to', REPORT_OUT)
    print('Original social score:', orig_social)
    print('New social_via_engine score:', new_social)
    print('Final percentage (with social engine):', f'{pct:.1f}%')


if __name__ == '__main__':
    main()
