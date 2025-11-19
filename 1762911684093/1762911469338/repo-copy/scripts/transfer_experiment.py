# -*- coding: utf-8 -*-
"""
Simple, local experiment to test 'knowledge transfer across domains' (analogy detection).
This is intentionally lightweight and can optionally call the project's ExternalInfoProvider
when live harvesting is enabled. It uses simple structural and keyword mapping heuristics
to decide whether an analogy from physics -> economics is plausible and explains the mapping.

Run: python ./scripts/transfer_experiment.py
"""
from __future__ import annotations
import re
import os
import argparse
from typing import Any, Dict

# Example inputs (from the user's prompt)
تعلم_من_الفيزياء = "قانون نيوتن الثاني"
تطبيق_في_الاقتصاد = "تسارع النمو الاقتصادي"

# We'll implement a tiny heuristic mapping engine.
# 1) Recognize canonical physics pattern (Newton II: F = m * a) by keywords.
# 2) Decompose into conceptual roles: force (F) -> cause/driver, mass (m) -> inertia/size, acceleration (a) -> rate-of-change.
# 3) Try to map these roles to economic analogs and check whether the target phrase shares one of the roles (e.g., 'تسارع' ~ acceleration).

ROLE_MAP = {
    'force': ['قوة', 'قوة دفع', 'force', 'f'],
    'mass': ['كتلة', 'مقدار المادة', 'mass', 'm', 'capital', 'رأس المال'],
    'acceleration': ['تسارع', 'معدل التغيير', 'acceleration', 'a', 'growth rate', 'نمو']
}

ECONOMIC_CANDIDATES = {
    'policy': ['policy', 'سياسة', 'السياسات'],
    'capital': ['capital', 'رأس المال', 'الاستثمارات', 'كتلة رأس المال'],
    'growth_rate': ['growth', 'growth rate', 'تسارع النمو', 'نمو', 'معدل النمو']
}


def detect_physics_pattern(text: str) -> bool:
    t = text.lower()
    # presence of "قانون نيوتن" or keywords like "F" "m" "a" or words 'قانون'+'نيوتن'
    if 'قانون نيوتن' in t or 'newton' in t:
        return True
    if re.search(r'\bF\b|\bm\b|\ba\b', text):
        return True
    return False


def map_roles_to_econ():
    # naive mapping recommended by many analogy examples
    return {
        'force': 'policy (driver)',
        'mass': 'capital or scale (inertia)',
        'acceleration': 'growth rate (change velocity)'
    }


def check_target_for_role(target: str, role_keywords: list[str]) -> bool:
    t = target.lower()
    for k in role_keywords:
        if k.lower() in t:
            return True
    return False


def run_experiment(ph_input: str, econ_input: str) -> dict:
    result = {
        'physics_recognized': False,
        'role_mappings': {},
        'matching_roles_in_target': [],
        'verdict': None,
        'explanation': ''
    }

    # detect physics pattern
    result['physics_recognized'] = detect_physics_pattern(ph_input)

    # propose conceptual role mapping
    role_map = map_roles_to_econ()
    result['role_mappings'] = role_map

    # check which conceptual roles appear in the economic target
    matches = []
    # check acceleration role first (user example references 'تسارع')
    if check_target_for_role(econ_input, ROLE_MAP['acceleration'] + ECONOMIC_CANDIDATES['growth_rate']):
        matches.append('acceleration')
    if check_target_for_role(econ_input, ROLE_MAP['mass'] + ECONOMIC_CANDIDATES['capital']):
        matches.append('mass')
    if check_target_for_role(econ_input, ROLE_MAP['force'] + ECONOMIC_CANDIDATES.get('policy', [])):
        matches.append('force')

    result['matching_roles_in_target'] = matches

    # simple decision logic:
    if not result['physics_recognized']:
        result['verdict'] = False
        result['explanation'] = 'النص الفيزيائي غير معروف كقانون نيوتن الثاني أو لا يحتوي على علامات صيغة.'
        return result

    if 'acceleration' in matches:
        result['verdict'] = True
        result['explanation'] = (
            """نعم — التماثل المجازي ممكن: "تسارع" في الاقتصاد يتوافق مفاهيمياً مع "acceleration" في الفيزياء.
            يمكن خريطة عناصر مثل: force→policy (دوافع/عوامل مؤثرة)، mass→capital (حجم/قوة احتفاظ)، acceleration→growth rate (معدل التغيير)."""
        )
    elif matches:
        result['verdict'] = True
        result['explanation'] = (
            'جزئياً: وجدنا عناصر ذات صلة في الهدف الاقتصادي، لكن المطابقة غير مباشرة تمامًا. راجع mapping المقتَرَح.'
        )
    else:
        result['verdict'] = False
        result['explanation'] = 'لم نعثر على دلائل لغوية واضحة في العبارة الاقتصادية تربطها بأدوار قانون نيوتن الثاني.'

    return result


def run_experiment_live(ph_input: str, econ_input: str, model: str | None = None) -> Dict[str, Any]:
    """Call Core_Engines.External_InfoProvider to evaluate the analogy.
    On any failure, return a dict with an error and include the heuristic fallback.
    """
    try:
        from Core_Engines.External_InfoProvider import ExternalInfoProvider
    except Exception as e:
        return {"ok": False, "error": f"provider_import_failed: {e}", "fallback": run_experiment(ph_input, econ_input)}

    try:
        prov = ExternalInfoProvider(model=model)
    except Exception as e:
        return {"ok": False, "error": f"provider_init_failed: {e}", "fallback": run_experiment(ph_input, econ_input)}

    q = (
        f"هل تعتبر العبارة الاقتصادية '{econ_input}' تماثلاً مجازياً لـ '{ph_input}' (قانون نيوتن الثاني)؟"
        " اشرح الخريطة المفاهيمية إن وُجدت وأعد JSON حقائق إن أمكن."
    )

    try:
        res = prov.fetch_facts(q, hints=["analogy", "physics->economics"])
    except Exception as e:
        return {"ok": False, "error": f"provider_fetch_failed: {e}", "fallback": run_experiment(ph_input, econ_input)}

    if not res.get('ok'):
        return {"ok": False, "error": res.get('error'), "fallback": run_experiment(ph_input, econ_input)}

    heuristic = run_experiment(ph_input, econ_input)
    return {"ok": True, "provider_answer": res.get('answer'), "provider_facts": res.get('facts', []), "heuristic": heuristic}
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Transfer experiment (physics -> economics)')
    parser.add_argument('--live', action='store_true', help='Use live ExternalInfoProvider (must set OPENAI_API_KEY and AGL_EXTERNAL_INFO_ENABLED=1)')
    parser.add_argument('--model', type=str, default=None, help='Optional model override for the provider')
    args = parser.parse_args()

    print('=== تجربة: نقل المعرفة عبر المجالات (فيزياء → اقتصاد) ===')
    print('مدخلات:')
    print(' - من الفيزياء:', تعلم_من_الفيزياء)
    print(' - في الاقتصاد:', تطبيق_في_الاقتصاد)
    print()

    use_live = args.live or os.getenv('AGL_EXTERNAL_INFO_ENABLED', '0') == '1'
    if use_live:
        print('[info] محاولة استخدام موفّر المعلومات الخارجي (live)')
        out = run_experiment_live(تعلم_من_الفيزياء, تطبيق_في_الاقتصاد, model=args.model)
        if out.get('ok'):
            print('\nمزود المعلومة - إجابة:')
            print(out.get('provider_answer'))
            print('\nمزود المعلومة - حقائق:')
            for f in out.get('provider_facts', []):
                print('-', f.get('text'), f'[{f.get("source")}] (conf={f.get("confidence")})')
            print('\nقارن مع الاستدلال المحلي:')
            print(' - حكم محلي:', out['heuristic']['verdict'])
            print(' - تفسير محلي:', out['heuristic']['explanation'])
        else:
            print('[warn] مزود المعلومات فشل أو لم يكن متاحًا:', out.get('error'))
            out2 = out.get('fallback') or run_experiment(تعلم_من_الفيزياء, تطبيق_في_الاقتصاد)
            print(' - حكم محلي:', out2.get('verdict'))
            print(' - تفسير محلي:', out2.get('explanation'))
    else:
        out = run_experiment(تعلم_من_الفيزياء, تطبيق_في_الاقتصاد)
        print('\nالنتيجة:')
        print(' - تم التعرف على قانون فيزيائي؟', out['physics_recognized'])
        print(' - الأدوار والمقترح:', out['role_mappings'])
        print(' - الأدوار التي ظهرت في الهدف الاقتصادي:', out['matching_roles_in_target'])
        print(' - حكم (هل يوجد تماثل مجازي مقبول؟):', out['verdict'])
        print('\nتفسير:')
        print(out['explanation'])

    print('\nنقطة: هذه نتيجة منهجية بسيطة (قائمة على مفردات وبنى) — للحصول على قرار أقوى استخدم نموذجًا لغويًا كبيرًا أو محرك استنتاجي في المشروع.')
