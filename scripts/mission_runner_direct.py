#!/usr/bin/env python3
"""Direct runner that calls mission_control_enhanced.process_with_unified_agi
for each evaluation question and saves results to `artifacts/mission_direct_results.json`.
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


def main():
    # ensure repo-copy importable
    repo_copy = os.path.abspath(os.path.join(HERE, '..', 'repo-copy'))
    if repo_copy not in sys.path:
        sys.path.insert(0, repo_copy)

    # Ensure legacy logging helper names exist in builtins to avoid NameError
    try:
        import builtins as _builtins
        if not hasattr(_builtins, '_append_log_line'):
            def _append_log_line(line: str):
                try:
                    pass
                except Exception:
                    pass
            _builtins._append_log_line = _append_log_line
        # historical misspellings
        _builtins._apppend_log_line = _builtins._append_log_line
        _builtins._appendd_log_line = _builtins._append_log_line
    except Exception:
        pass

    out = {"started_at": time.time(), "questions": []}

    try:
        from dynamic_modules.mission_control_enhanced import process_with_unified_agi
    except Exception as e:
        print(f"Failed to import mission_control_enhanced: {e}")
        sys.exit(2)

    for qid, prompt in QUESTIONS:
        print(f"Running {qid}...")
        start = time.time()
        try:
            # run coroutine
            from asyncio import run as _run
            res = _run(process_with_unified_agi(prompt))
            dur = time.time() - start
            # extract answer text
            if isinstance(res, dict):
                ans = res.get('reply') or res.get('final_response') or res.get('raw') or res
            else:
                ans = str(res)
        except Exception as e:
            ans = f"<error: {e}>"
            dur = time.time() - start

        out['questions'].append({
            'id': qid,
            'prompt': prompt,
            'answer': ans,
            'response_time_sec': round(dur, 4)
        })

    out['finished_at'] = time.time()
    os.makedirs(HERE.parent / 'artifacts', exist_ok=True)
    out_path = HERE.parent / 'artifacts' / 'mission_direct_results.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"Saved results to {out_path}")


if __name__ == '__main__':
    main()
