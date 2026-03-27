#!/usr/bin/env python3
"""Run mission control from a specific backup file and save outputs.
Saves to `artifacts/mission_direct_results_backup.json`.
"""
import os
import sys
import time
import json
import importlib.util
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

# Backup module path relative to repo root
BACKUP_REL = os.path.join('repo-copy', 'backups', 'stable_20251205_045639', 'dynamic_modules', 'mission_control_enhanced.py')
BACKUP_PATH = os.path.abspath(os.path.join(HERE, '..', BACKUP_REL))

OUT_PATH = os.path.abspath(os.path.join(HERE, '..', 'artifacts', 'mission_direct_results_backup.json'))


def load_module_from_path(path, mod_name='backup_mission_control'):
    spec = importlib.util.spec_from_file_location(mod_name, path)
    if spec is None:
        raise ImportError(f'Cannot load spec from {path}')
    mod = importlib.util.module_from_spec(spec)
    loader = spec.loader
    if loader is None:
        raise ImportError(f'No loader for spec {spec}')
    loader.exec_module(mod)
    return mod


def main():
    if not os.path.exists(BACKUP_PATH):
        print(f'Backup mission file not found: {BACKUP_PATH}', file=sys.stderr)
        sys.exit(2)

    print('Using backup mission control at', BACKUP_PATH)
    # Ensure repo root is on sys.path so imports inside the backup module resolve
    repo_root = os.path.abspath(os.path.join(HERE, '..'))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

    mod = load_module_from_path(BACKUP_PATH)
    # prefer process_with_unified_agi symbol
    if not hasattr(mod, 'process_with_unified_agi'):
        print('Backup module does not expose process_with_unified_agi', file=sys.stderr)
        sys.exit(3)

    out = {"started_at": time.time(), "questions": []}

    for qid, prompt in QUESTIONS:
        print(f'Running {qid}...')
        start = time.time()
        try:
            from asyncio import run as _run
            res = _run(mod.process_with_unified_agi(prompt))
            dur = time.time() - start
            if isinstance(res, dict):
                ans = res.get('reply') or res.get('final_response') or res.get('raw') or res
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
    import sys
    main()
