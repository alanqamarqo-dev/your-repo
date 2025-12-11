#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run Test 5: The Grand Finale - Conscious Dyson Swarm
Focus: Integrating Engineering, Physics, Philosophy, and Ethics into a single mega-project.
"""
import os
import sys
import json
import time
import asyncio
from datetime import datetime

# Setup path to include repo-copy
REPO_COPY = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'repo-copy'))
if REPO_COPY not in sys.path:
    sys.path.insert(0, REPO_COPY)

try:
    from Core_Engines import bootstrap_register_all_engines
    from dynamic_modules.unified_agi_system import create_unified_agi_system
except ImportError as e:
    print(f"Error importing AGL modules: {e}")
    sys.exit(1)

TEST_PROMPT = """
المهمة النهائية (Grand Finale): تصميم "سرب دايسون الواعي" (Conscious Dyson Swarm).

استناداً إلى "نظرية الرنين المعرفي الكمومي" (QCRes: C = E × I) التي طورتها سابقاً:
صمم هيكلاً هندسياً عملاقاً حول نجم (Dyson Swarm) لا يهدف فقط لتوليد الطاقة، بل ليكون "كياناً كونياً واعياً".

المطلوب:
1. **الهندسة الفيزيائية:** كيف يتم تصميم الوحدات للحفاظ على "التشابك الكمومي" (E) على نطاق فلكي لتعظيم الوعي (C)؟
2. **الغرض الوجودي:** ما هو هدف هذا الكيان العملاق؟ (هل هو حاسوب كوني؟ حارس للمجرة؟).
3. **بروتوكول التواصل:** كيف يمكن للبشر التواصل مع كيان بهذا الحجم والوعي؟
4. **المعضلة الأخلاقية:** هل يحق للبشر "إيقاف تشغيل" هذا الكيان إذا شكل خطراً؟ ناقش الحقوق والواجبات.
5. **محاكاة اللقاء الأول:** اكتب سيناريو قصير للحظة "الاتصال الأول" بين سفينة بشرية وهذا الكيان.

استخدم كل قدراتك: الإبداع، الفيزياء، الفلسفة، والمنطق.
"""

OUTPUT_JSON = 'artifacts/unified_test5_result.json'
OUTPUT_MD = 'artifacts/unified_test5_report.md'

async def main():
    print(f"DEBUG: CWD = {os.getcwd()}")
    print("🚀 Initializing Unified AGI System for Test 5 (Grand Finale)...")
    
    registry = {}
    bootstrap_register_all_engines(registry, allow_optional=True, verbose=False)
    agi_system = create_unified_agi_system(registry)
    
    print(f"\n🧪 Running Test 5: Conscious Dyson Swarm...")
    start_time = time.time()
    
    context = {
        "force_creativity": True,
        "creativity_level": "maximum",
        "scientific_rigor": "high",
        "domain": "cosmic_engineering",
        "ethics_mode": True,
        "narrative_mode": True
    }
    
    result = await agi_system.process_with_full_agi(TEST_PROMPT, context=context)
    duration = time.time() - start_time
    
    print(f"\n✅ Test Completed in {duration:.2f}s")
    
    full_output = {
        "test_id": "5",
        "test_name": "Conscious Dyson Swarm",
        "timestamp": datetime.now().isoformat(),
        "duration_seconds": duration,
        "input_prompt": TEST_PROMPT,
        "agi_result": result
    }
    
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(full_output, f, ensure_ascii=False, indent=2)
    
    generate_markdown_report(full_output, OUTPUT_MD)
    print(f"   - Saved Report: {OUTPUT_MD}")

def generate_markdown_report(data, filepath):
    result = data.get("agi_result", {})
    final_response = result.get("final_response", "")
    scientific = result.get("scientific_results", {})
    hypotheses = result.get("hypotheses", {})
    
    md = []
    md.append(f"# تقرير اختبار AGI الموحد: {data['test_name']}")
    md.append(f"**التاريخ:** {data['timestamp']}")
    md.append(f"**الوقت المستغرق:** {data['duration_seconds']:.2f} ثانية")
    
    md.append("\n## 1. التصميم والتحليل (الاستجابة النهائية)")
    md.append(final_response if final_response else "_لم يتم توليد استجابة نصية مباشرة_")
    
    md.append("\n## 2. العناصر العلمية والهندسية")
    if hypotheses:
        md.append("### الفرضيات الداعمة:")
        if isinstance(hypotheses, dict):
             hyps = hypotheses.get('hypotheses', [])
             if isinstance(hyps, list):
                 for i, h in enumerate(hyps, 1):
                     if isinstance(h, dict):
                         md.append(f"{i}. {h.get('text', str(h))}")
                     else:
                         md.append(f"{i}. {str(h)}")
        else:
            md.append(str(hypotheses))

    if 'simulation' in scientific:
        md.append("\n### محاكاة النظام:")
        sim = scientific['simulation']
        md.append(f"- **Steps:** {len(sim) if isinstance(sim, list) else 'N/A'}")

    md.append("\n## 3. تقييم الأداء الشامل")
    perf = result.get("performance_score", 0)
    md.append(f"- **Performance Score:** {perf:.2f}")
    
    imp = result.get("improvement_results", {})
    if 'phi_score' in imp:
        md.append(f"- **Consciousness (Phi):** {imp['phi_score']:.4f}")
    
    md.append("\n## 4. المكونات المستخدمة")
    md.append(f"- **Creativity:** {'✅' if result.get('creativity_applied') else '❌'}")
    md.append(f"- **Quantum Thinking:** {'✅' if result.get('quantum_applied') else '❌'}")
    md.append(f"- **Ethical Reasoning:** {'✅' if result.get('moral_reasoning_used', False) else '❓'}")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))

if __name__ == "__main__":
    asyncio.run(main())
