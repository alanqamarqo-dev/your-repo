import os
import json
from pathlib import Path
from Self_Improvement.medical_qa_fast import medical_qa_fast

OUT_DIR = Path(__file__).resolve().parents[1] / 'artifacts' / 'medical_fast_outputs'
OUT_DIR.mkdir(parents=True, exist_ok=True)

questions = [
    "ما هي مخاطر استخدام الأدوية المهرّبة على مرضى الفشل الكلوي؟",
    "ما آثار الاستخدام الطويل لمضادات الالتهاب غير الستيرويدية (NSAIDs) على مرضى ارتفاع ضغط الدم؟",
    "ما العلاقة بين سوء تخزين الدواء وفعاليته العلاجية، وكيف تؤثر درجات الحرارة والرطوبة؟",
    "ما الاعتبارات الدوائية عند تناول أدوية متعددة لدى مرضى الكِلى المزمنة (polypharmacy)، وما أهم التداخلات التي يجب تجنبها؟",
    "ما الإجراءات العملية للتقليل من أضرار تداول الأدوية غير المسجلة في المجتمعات الريفية (تثقيف، مراقبة، بدائل متاحة)?",
]

results = []
for i, q in enumerate(questions, start=1):
    try:
        res = medical_qa_fast(q, timeout_s=15, max_points=6, max_words=400)
    except Exception as e:
        res = {"answer": "", "error": str(e)}
    path = OUT_DIR / f"q_{i}.json"
    with path.open('w', encoding='utf-8') as f:
        json.dump({'question': q, 'result': res}, f, ensure_ascii=False, indent=2)
    print(f"Wrote: {path}")
    results.append({'question': q, 'result': res})

# write combined
combined = OUT_DIR / 'combined_results.json'
with combined.open('w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"Combined results written to: {combined}")
