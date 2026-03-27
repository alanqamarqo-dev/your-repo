"""Run UnifiedAGISystem on impossible questions (workspace-level runner).

This runner invokes `repo-copy/dynamic_modules/unified_agi_system.py` by
ensuring `repo-copy` is on `sys.path`. It saves results to
`D:/AGL/artifacts/unified_impossible_results.json`.
"""
import sys
import json
from pathlib import Path

# Ensure repo-copy is importable
sys.path.insert(0, r"d:\AGL\repo-copy")

try:
    from dynamic_modules.unified_agi_system import UnifiedAGISystem
except Exception:
    UnifiedAGISystem = None

from pathlib import Path

PROMPTS = [
    # (shortened duplicate of repo-copy version; keep same questions)
    {"id": 1, "title": "طبيعة الزمن", "text": "..."},
    {"id": 2, "title": "ما قبل الانفجار العظيم", "text": "..."},
    {"id": 3, "title": "طبيعة الوعي", "text": "..."},
    {"id": 4, "title": "مفارقة فيرمي", "text": "..."},
    {"id": 5, "title": "المادة والطاقة المظلمة", "text": "..."},
    {"id": 6, "title": "أصل الحياة", "text": "..."},
    {"id": 7, "title": "الانفجار الكامبري", "text": "..."},
    {"id": 8, "title": "النوم والأحلام", "text": "..."},
    {"id": 9, "title": "فرضية ريمان", "text": "..."},
    {"id":10, "title": "P vs NP", "text": "..."},
    {"id":11, "title": "لماذا يوجد شيء", "text": "..."},
    {"id":12, "title": "طبيعة الرياضيات", "text": "..."},
    {"id":13, "title": "الإرادة الحرة", "text": "..."},
    {"id":14, "title": "مشكلة القياس في الكم", "text": "..."},
    {"id":15, "title": "التشابك والتأثير عن بعد", "text": "..."},
    {"id":16, "title": "تفسير العوالم المتعددة", "text": "..."},
]

OUT_FILE = Path(r"D:\AGL\artifacts\unified_impossible_results.json")
OUT_FILE.parent.mkdir(parents=True, exist_ok=True)

results = []

if UnifiedAGISystem is None:
    print("UnifiedAGISystem not available at repo-copy; aborting.")
    raise SystemExit(1)

# Use Core_Engines registry if available
try:
    from Core_Engines import ENGINE_REGISTRY
except Exception:
    ENGINE_REGISTRY = {}

agi = UnifiedAGISystem(ENGINE_REGISTRY)

for p in PROMPTS:
    print("Processing:", p['title'])
    try:
        resp = agi.process_with_full_agi(p['text'])
        # Await if coroutine
        import asyncio
        if asyncio.iscoroutine(resp):
            resp = asyncio.run(resp)
    except Exception as e:
        resp = {"error": str(e)}
    results.append({"id": p['id'], "title": p['title'], "response": resp})

with open(OUT_FILE, 'w', encoding='utf-8') as fh:
    json.dump(results, fh, ensure_ascii=False, indent=2)

print('Saved results to', OUT_FILE)
