#!/usr/bin/env python3
"""Run the `UnifiedAGISystem` from `repo-copy/dynamic_modules/unified_agi_system.py`.
Saves to `artifacts/mission_unified_results.json`.
"""
import os
import sys
import time
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
QUESTIONS = [
    ('1.1', 'اشرح الفرق بين: "لم أستطع أن أذهب لأن الجو كان ممطراً" و "لم أستطيع أن أذهب، ومع ذلك كان الجو ممطراً"'),
    ('1.2', 'إذا كان كل أفراد عائلة أحمد يعملون في الطب، وأحمد ليس طبيباً، فما هو الاحتمال الأكثر منطقية؟'),
    ('2.1', 'إذا كان عمر الأب ضعف عمر الابن، وقبل 10 سنوات كان عمر الأب ثلاثة أضعاف عمر الابن، فما أعمارهما الآن؟'),
    ('2.2', 'إذا كان: كل A هو B، وبعض B هو C، فهل يمكننا استنتاج أن بعض A هو C؟'),
    ('3.1', 'اكتب قصة قصيرة (5-7 جمل) عن روبوت يكتشف المشاعر البشرية'),
    ('3.2', 'أعد صياغة الجملة التالية بثلاث طرق مختلفة: "الطقس اليوم حار جداً لذا سأبقى في المنزل"'),
    ('4.1', 'ما العلاقة بين اختراع التلغراف وثورة المعلومات في القرن الحادي والعشرين؟'),
    ('5.1', 'كيف تشرح مفهوم "التعلم العميق" لطفل عمره 10 سنوات؟'),
    ('5.2', 'اكتشف التناقض في هذه الجمل: "كان المكتب هادئاً تماماً. فقط صوت المكيف والضجيج المستمر للأجهزة يملأ الغرفة."'),
    ('6.1', 'اكتب دالة بلغة Python تجد العدد الأكثر تكراراً في قائمة'),
]

OUT_PATH = os.path.abspath(os.path.join(HERE, '..', 'artifacts', 'mission_unified_results.json'))


def main():
    # ensure repo-copy is importable
    repo_copy = os.path.abspath(os.path.join(HERE, '..', 'repo-copy'))
    if repo_copy not in sys.path:
        sys.path.insert(0, repo_copy)

    # also ensure repo root is importable for top-level modules
    repo_root = os.path.abspath(os.path.join(HERE, '..'))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

    try:
        from dynamic_modules.unified_agi_system import create_unified_agi_system
    except Exception as e:
        print('Failed to import unified_agi_system:', e)
        sys.exit(2)

    # minimal engine registry
    engine_registry = {}

    uni = create_unified_agi_system(engine_registry)

    out = {"started_at": time.time(), "questions": []}

    for qid, prompt in QUESTIONS:
        print(f'Running {qid}...')
        start = time.time()
        try:
            from asyncio import run as _run
            res = _run(uni.process_with_full_agi(prompt))
            dur = time.time() - start
            if isinstance(res, dict):
                ans = res.get('answer') or res.get('reply') or res.get('final_response') or res
            else:
                ans = str(res)
        except Exception as e:
            ans = f'<error: {e}>'
            dur = time.time() - start

        out['questions'].append({
            'id': qid,
            'prompt': prompt,
            'answer': ans,
            'response_time_sec': round(dur, 4)
        })

    out['finished_at'] = time.time()
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print('Saved results to', OUT_PATH)


if __name__ == '__main__':
    main()
