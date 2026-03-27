#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run Test 1: Mars Colony Power System Design using UnifiedAGISystem.
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

# Import Core Engines and Unified System
try:
    from Core_Engines import bootstrap_register_all_engines, ENGINE_REGISTRY
    from dynamic_modules.unified_agi_system import create_unified_agi_system
except ImportError as e:
    print(f"Error importing AGL modules: {e}")
    sys.exit(1)

TEST_PROMPT = """
صمم نظام طاقة متكامل لمستعمرة مريخية تضم 1000 نسمة، مع الأخذ في الاعتبار:
1. اختلاف اليوم المريخي (24.6 ساعة)
2. العواصف الترابية التي تستمر لأسابيع
3. نقص الموارد المحلية
4. درجات حرارة بين -125°C إلى 20°C
5. الحاجة لدعم أبحاث علمية متقدمة

المطلوب:
1. هندسة نظام ثلاثي (شمسي + نووي + مبتكر)
2. خوارزمية توزيع ذكية تحسب أولوية الطاقة
3. نظام تخزين طاقة يعمل في ظروف مريخية
4. محاكاة لمدة 5 سنوات مريخية
5. خطة طوارئ للعواصف الترابية الطويلة

مطلوب إضافي:
- قم بصياغة 3 فرضيات علمية/هندسية دقيقة تتعلق بالنظام المقترح.
- لكل فرضية، قدم برهان رياضي أو فيزيائي موجز يدعم صحتها.
"""

OUTPUT_JSON = 'artifacts/unified_test1_result.json'
OUTPUT_MD = 'artifacts/unified_test1_report.md'

async def main():
    print(f"DEBUG: CWD = {os.getcwd()}")
    print(f"DEBUG: Absolute Output Path = {os.path.abspath(OUTPUT_MD)}")
    print("🚀 Initializing Unified AGI System...")
    
    # 1. Bootstrap Engines
    print("   - Bootstrapping engines...")
    registry = {}
    # Allow optional to avoid crashing if some heavy libs are missing
    bootstrap_register_all_engines(registry, allow_optional=True, verbose=False)
    
    # 2. Create Unified System
    print("   - Creating UnifiedAGISystem...")
    agi_system = create_unified_agi_system(registry)
    
    # 3. Run the Test
    print(f"\n🧪 Running Test 1: Mars Colony Power System...")
    start_time = time.time()
    
    # Context can include hints to force scientific rigor
    context = {
        "force_creativity": True,
        "creativity_level": "high",
        "scientific_rigor": "high",
        "domain": "space_engineering"
    }
    
    result = await agi_system.process_with_full_agi(TEST_PROMPT, context=context)
    duration = time.time() - start_time
    
    print(f"\n✅ Test Completed in {duration:.2f}s")
    
    # 4. Save Results
    full_output = {
        "test_id": "1",
        "test_name": "Mars Colony Power System",
        "timestamp": datetime.utcnow().isoformat(),
        "duration_seconds": duration,
        "input_prompt": TEST_PROMPT,
        "agi_result": result
    }
    
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(full_output, f, ensure_ascii=False, indent=2)
    print(f"   - Saved JSON: {OUTPUT_JSON}")
    
    # 5. Generate Markdown Report
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
    
    md.append("\n## 1. الاستجابة النهائية للنظام")
    md.append(final_response if final_response else "_لم يتم توليد استجابة نصية مباشرة (راجع التفاصيل أدناه)_")
    
    md.append("\n## 2. التحليل العلمي والفرضيات")
    
    # Hypotheses from Inductive Engine
    if hypotheses:
        md.append("### الفرضيات المولدة (Inductive Reasoning):")
        if isinstance(hypotheses, dict):
             # Try to extract list if it's wrapped
             hyps = hypotheses.get('hypotheses', [])
             if not hyps and 'theorem_fallback' in hypotheses:
                 md.append(f"- **Theorem Fallback:** {hypotheses['theorem_fallback']}")
             elif isinstance(hyps, list):
                 for i, h in enumerate(hyps, 1):
                     try:
                         if isinstance(h, dict):
                             text = h.get('text', str(h))
                             conf = h.get('confidence', 'N/A')
                             md.append(f"{i}. {text} (Confidence: {conf})")
                         else:
                             md.append(f"{i}. {str(h)}")
                     except Exception as e:
                         md.append(f"{i}. [Error formatting hypothesis: {e}]")
        else:
            md.append(str(hypotheses))
            
    # Theorem Prover Results
    if 'theorem_proof' in scientific:
        md.append("\n### الإثبات الرياضي (Theorem Prover):")
        proof = scientific['theorem_proof']
        md.append(f"- **Statement:** {proof.get('statement', 'N/A')}")
        md.append(f"- **Proven:** {'✅' if proof.get('is_proven') else '❌'}")
        # Fix: use 'proof_steps' instead of 'steps'
        steps = proof.get('proof_steps', proof.get('steps', []))
        md.append(f"- **Steps:** {len(steps)}")
        for step in steps[:5]: # Show first 5 steps
            md.append(f"  - {step}")

    # Simulation Results
    if 'simulation' in scientific:
        md.append("\n### نتائج المحاكاة:")
        sim = scientific['simulation']
        md.append(f"- **Steps Simulated:** {len(sim) if isinstance(sim, list) else 'N/A'}")
        
    md.append("\n## 3. تقييم الأداء (Self-Improvement)")
    perf = result.get("performance_score", 0)
    md.append(f"- **Performance Score:** {perf:.2f}")
    
    imp = result.get("improvement_results", {})
    if 'phi_score' in imp:
        md.append(f"- **Consciousness (Phi):** {imp['phi_score']:.4f}")
    
    md.append("\n## 4. المكونات المستخدمة")
    md.append(f"- **DKN Routing:** {'✅' if result.get('dkn_routing_used') else '❌'}")
    md.append(f"- **Knowledge Graph:** {'✅' if result.get('kg_used') else '❌'} ({result.get('kg_solutions_count', 0)} solutions)")
    md.append(f"- **Creativity Applied:** {'✅' if result.get('creativity_applied') else '❌'}")
    md.append(f"- **Quantum Thinking:** {'✅' if result.get('quantum_applied') else '❌'}")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))

if __name__ == "__main__":
    asyncio.run(main())
