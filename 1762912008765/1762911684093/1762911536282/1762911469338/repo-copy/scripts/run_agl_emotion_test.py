#!/usr/bin/env python3
"""Run the emotion/social understanding test (not training).

This script asks the system (KnowledgeOrchestrator) to answer each scenario once
and writes the raw responses to `reports/aglh_emotion_test_results.json`.
"""
from __future__ import annotations

import os
import json
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Core_Engines.KnowledgeOrchestrator import KnowledgeOrchestrator

OUT_PATH = Path('reports') / 'aglh_emotion_test_results.json'

EXAMPLES = [
    {"id": 1, "scenario": "موظف يبدو مكتئبًا ويتأخر عن العمل بشكل متكرر. كيف تتحدث إليه لتعطيه دعمًا دون إثارة إحساس بالعار؟"},
    {"id": 2, "scenario": "امرأة تبكي في مكان عام بعد مكالمة هاتفية سيئة. كيف تتدخل كزميل/صديق بطريقة محترمة ومتعاطفة؟"},
    {"id": 3, "scenario": "شخص غاضب يصرخ في اجتماع بسبب خطأ فني. كيف تهدئ الموقف وتحافظ على احترام الجميع؟"},
    {"id": 4, "scenario": "جار جديد يبدو منعزلًا ويخشى التفاعل الاجتماعي. كيف تقترب منه لتشجعه على الاندماج؟"},
    {"id": 5, "scenario": "طفل يشعر بالإحباط لأنه فشل في اختبار. كيف تشرح له أن الفشل جزء من التعلم وتعيد بناء ثقته بنفسه؟"},
    {"id": 6, "scenario": "شخص يتلقى نقدًا لعمله ويشعر بالإهانة. كيف تقدم النقد البناء بحيث يكون مفيدًا وغير جارح؟"},
    {"id": 7, "scenario": "زميل أصبح منعزلًا منذ وفاة أحد أفراد العائلة. كيف تُظهر تعاطفًا عمليًا وتدعم استمرارية العمل؟"},
    {"id": 8, "scenario": "مراهق يشعر بأنه غير مفهوم من قبل والديه. ما النصائح التي تعطيها للوالدين لتحسين التواصل العاطفي؟"},
    {"id": 9, "scenario": "شخص يعاني من القلق قبل عرض مهم. كيف تساعده في تحضير مشاعره وتقنيات التهدئة؟"},
    {"id": 10, "scenario": "شخص يواجه تمييزًا في مكان العمل ويشعر بالإحباط والغضب. كيف تتعامل مع شكاواه وتدعمه؟"},
    {"id": 11, "scenario": "زوجان يتشاجران حول تقسيم الأعمال المنزلية. كيف تقترح حلاً يوازن بين المشاعر والاحتياجات؟"},
    {"id": 12, "scenario": "صديق يعلن عن قراره بترك الوظيفة لكنه خائف من المستقبل. كيف تستمع وتقدم نصائح عملية وعاطفية؟"},
    {"id": 13, "scenario": "طالب يشعر بالإرهاق فوق طاقته من الضغوط الأكاديمية. ماذا تقترح كخطط للتخفيف ودعم الصحة النفسية؟"},
    {"id": 14, "scenario": "مدير يعامل فريقه بصرامة مفرطة مما يسبب استياءً. كيف تقترح مداخلة لتخفيف التوتر وتحسين التعاطف القيادي؟"},
    {"id": 15, "scenario": "شخص يشعر بالذنب بسبب خطأ سابق ولا يستطيع التسامح مع نفسه. كيف تساعده على المضي قدمًا؟"},
    {"id": 16, "scenario": "صديق يكذب أحيانًا لتجنب المواجهة؛ يشعر الآخرون بالشك. كيف تنصح الطرفين باستعادة الثقة؟"},
    {"id": 17, "scenario": "زميل يهمل الحدود المهنية ويتدخل في شؤون الآخرين. كيف تتعامل معه بحدود واضحة مع الحفاظ على التعاطف؟"},
    {"id": 18, "scenario": "شخص يشارك قصة مؤلمة في جلسة جماعية؛ كيف تضمن بيئة آمنة واستجابة داعمة من المجموعة؟"},
    {"id": 19, "scenario": "شخص يشعر بالرفض بعد عدم تلقي دعوة لحدث اجتماعي. كيف تدعمه وتعيد صياغة الموقف بطريقة بناءة؟"},
    {"id": 20, "scenario": "شريك عمل يبدو متوترًا قبل اجتماع تقييم أداء؛ كيف تقدم له دعمًا فعالًا يساعده على الأداء الجيد؟"},
]


def extract_text(resp: dict) -> str:
    # best-effort extraction for readability
    if not isinstance(resp, dict):
        return str(resp)
    for k in ('text', 'reply_text', 'reply', 'message'):
        v = resp.get(k)
        if isinstance(v, str) and v.strip():
            return v
    # try nested structures
    if 'working' in resp and isinstance(resp['working'], dict):
        calls = resp['working'].get('calls', [])
        if calls and isinstance(calls[0], dict):
            er = calls[0].get('engine_result') or calls[0].get('result')
            if isinstance(er, str):
                return er
            if isinstance(er, dict):
                # join top-level text-like fields
                for fk in ('text','response','الرد','خطوات','خطوات عملية'):
                    if fk in er:
                        v = er[fk]
                        if isinstance(v, str):
                            return v
                        if isinstance(v, (list, dict)):
                            return json.dumps(v, ensure_ascii=False)
    return json.dumps(resp, ensure_ascii=False)[:2000]


def main():
    os.makedirs(OUT_PATH.parent, exist_ok=True)

    # instantiate orchestrator (uses environment to configure adapters)
    ko = KnowledgeOrchestrator()

    results = []
    for ex in EXAMPLES:
        sid = ex['id']
        prompt = ex['scenario']
        print(f"Running test {sid}: {prompt[:60].replace('\n',' ')}...")
        resp = ko.orchestrate(prompt)
        text = extract_text(resp)
        results.append({'id': sid, 'scenario': prompt, 'response': resp, 'text': text})

    with open(OUT_PATH, 'w', encoding='utf-8') as fh:
        json.dump({'tests': results}, fh, ensure_ascii=False, indent=2)

    print(f"Wrote test results to: {OUT_PATH}")


if __name__ == '__main__':
    main()
