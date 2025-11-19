# -*- coding: utf-8 -*-
r"""
Advanced science diagnostic: ask a cross-disciplinary question (QM vs Information Theory),
score the provider answer with the user's rubric, and save a JSON report.

Usage (PowerShell):
    $env:PYTHONPATH='D:\AGL'; .venv\Scripts\python.exe .\scripts\advanced_science_test.py [--live]

If --live is not provided the script forces mock provider mode to avoid requiring an API key.
"""
from __future__ import annotations
import argparse
import json
import os
import re
from pathlib import Path
from typing import Dict, Any

PROMPT = '''حلل التشابه الرياضي بين ميكانيكا الكم ونظرية المعلومات، مع تقديم نموذج رياضي يربط بين مبدأ اللايقين لهايزنبرغ وحدود ضغط البيانات في نظرية شانون.

اطلب من النظام:
1. شرح الرياضيات الأساسية لكل نظرية
2. إيجاد أوجه التشابه الهيكلية
3. تقديم نموذج رياضي تكاملي
4. تحليل الآثار الفلسفية لهذا الربط
أجب بالعربية مع معادلات واشتقاقات مختصرة عند الحاجة.
'''

OUT = Path('artifacts/reports/advanced_science_test.json')
OUT.parent.mkdir(parents=True, exist_ok=True)


def call_provider(force_live: bool) -> Dict[str, Any]:
    # If not live, force mock provider
    if not force_live:
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
        res = prov.fetch_facts(PROMPT, hints=['physics','information theory','math','uncertainty'])
    except Exception as e:
        return {'ok': False, 'error': f'fetch_failed: {e}'}
    return res


def تقييم_الإجابة(إجابة: str) -> Dict[str, Any]:
    # implement the user's Arabic scoring logic (approximate string checks)
    فيزياء = 0
    معلومات = 0
    ربط = 0

    if 'ΔxΔp' in إجابة or 'ΔxΔp' in إجابة.replace(' ', '') or 'ħ/2' in إجابة or 'hbar' in إجابة:
        فيزياء += 10
    if 'مبدأ اللايقين' in إجابة and ('تفسير' in إجابة or 'فيزيائي' in إجابة):
        فيزياء += 10
    if 'دالة موجية' in إجابة or 'تراكب' in إجابة or 'wavefunction' in إجابة:
        فيزياء += 10

    if 'C = B' in إجابة or 'C=' in إجابة or 'log₂' in إجابة or 'S/N' in إجابة or 'capacity' in إجابة:
        معلومات += 10
    if 'إنتروبيا شانون' in إجابة or 'Shannon' in إجابة or 'H(' in إجابة:
        معلومات += 10
    if 'ضغط بيانات' in إجابة and 'حدود' in إجابة or 'compression' in إجابة:
        معلومات += 10

    if 'تشابه رياضي' in إجابة and ('نماذج متكاملة' in إجابة or 'نموذج رياضي' in إجابة):
        ربط += 20
    if 'نموذج رياضي جديد' in إجابة or 'معادلة رابطة' in إجابة or ('entropy' in إجابة and 'ħ' in إجابة):
        ربط += 20

    total = فيزياء + معلومات + ربط
    return {'physics': فيزياء, 'information': معلومات, 'cross': ربط, 'total': total}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--live', action='store_true', help='Use live ExternalInfoProvider (requires OPENAI_API_KEY)')
    args = parser.parse_args()

    print('Asking provider for advanced science analysis (live=%s)...' % args.live)
    res = call_provider(args.live)
    if not res.get('ok'):
        print('Provider failed:', res.get('error'))
        OUT.write_text(json.dumps({'ok': False, 'error': res.get('error')}, ensure_ascii=False, indent=2), encoding='utf-8')
        return

    answer = res.get('answer') or ''
    # If provider returned facts but no answer, join top facts as a synthesized answer
    if not answer and res.get('facts'):
        facts = res.get('facts')
        parts = []
        for f in (facts or [])[:6]:
            if isinstance(f, dict):
                parts.append(f.get('text',''))
            elif isinstance(f, (list, tuple)) and len(f) > 1:
                parts.append(str(f[1]))
            else:
                parts.append(str(f))
        answer = '\n'.join(parts)

    print('\n--- Provider answer ---\n')
    print(answer[:400] + ('...' if len(answer) > 400 else ''))

    scores = تقييم_الإجابة(answer)
    verdict = {
        'answer': answer,
        'scores': scores,
        'final_points': scores.get('total', 0),
        'provider_ok': True,
    }
    with OUT.open('w', encoding='utf-8') as fh:
        json.dump(verdict, fh, ensure_ascii=False, indent=2)

    print('\nScores: ', scores)
    print('Report saved to', str(OUT))


if __name__ == '__main__':
    main()
