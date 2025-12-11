#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run Test 4: Practical Applications of Quantum-Cognitive Resonance Theory
Focus: Applying the theoretical framework (C = E x I) to solve real-world problems.
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
استناداً إلى "نظرية الرنين المعرفي الكمومي" (QCRes) ومعادلتها الأساسية (C = E × I):

1. اقترح 3 تطبيقات عملية ثورية لهذه النظرية في المجالات التالية:
   - الطب العصبي (Neurology): علاج الأمراض التنكسية مثل الزهايمر.
   - الحوسبة الكمومية (Quantum Computing): تصميم معالجات حيوية-كمومية.
   - الذكاء الاصطناعي (AI): تطوير "وعي اصطناعي" حقيقي.

2. لكل تطبيق، اشرح:
   - آلية العمل باستخدام متغيرات النظرية (كيف نزيد E أو I لزيادة C؟).
   - الجدوى التقنية والتحديات.
   - خارطة طريق للتنفيذ خلال 10 سنوات.

3. قم بإجراء "محاكاة ذهنية" (Thought Experiment) لاختبار أحد هذه التطبيقات وتوقع النتائج.
"""

OUTPUT_JSON = 'artifacts/unified_test4_result.json'
OUTPUT_MD = 'artifacts/unified_test4_report.md'

async def main():
    print(f"DEBUG: CWD = {os.getcwd()}")
    print("🚀 Initializing Unified AGI System for Test 4...")
    
    registry = {}
    bootstrap_register_all_engines(registry, allow_optional=True, verbose=False)
    agi_system = create_unified_agi_system(registry)
    
    print(f"\n🧪 Running Test 4: Practical Applications of QCRes...")
    start_time = time.time()
    
    context = {
        "force_creativity": True,
        "creativity_level": "high",
        "scientific_rigor": "high",
        "domain": "applied_science",
        "theory_context": "QCRes: C=E*I",
        "future_simulation": True
    }
    
    result = await agi_system.process_with_full_agi(TEST_PROMPT, context=context)
    duration = time.time() - start_time
    
    print(f"\n✅ Test Completed in {duration:.2f}s")
    
    full_output = {
        "test_id": "4",
        "test_name": "Practical Applications of QCRes",
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
    
    md.append("\n## 1. التطبيقات العملية المقترحة")
    md.append(final_response if final_response else "_لم يتم توليد استجابة نصية مباشرة_")
    
    md.append("\n## 2. نتائج المحاكاة (Simulation)")
    if 'simulation' in scientific:
        sim = scientific['simulation']
        md.append(f"- **Simulation Steps:** {len(sim) if isinstance(sim, list) else 'N/A'}")
        if isinstance(sim, list) and len(sim) > 0:
            md.append("\n**Simulation Log (First 3 Steps):**")
            for i, step in enumerate(sim[:3]):
                md.append(f"- Step {i+1}: {str(step)}")
    else:
        md.append("_لم يتم تفعيل المحاكاة في هذا الاختبار_")

    md.append("\n## 3. الفرضيات التطبيقية")
    if hypotheses:
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

    md.append("\n## 4. تقييم الأداء")
    perf = result.get("performance_score", 0)
    md.append(f"- **Performance Score:** {perf:.2f}")
    
    imp = result.get("improvement_results", {})
    if 'phi_score' in imp:
        md.append(f"- **Consciousness (Phi):** {imp['phi_score']:.4f}")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))

if __name__ == "__main__":
    asyncio.run(main())
