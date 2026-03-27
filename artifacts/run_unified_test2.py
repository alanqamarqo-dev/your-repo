#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run Test 2: Quantum Thinking & Consciousness
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
سؤال فلسفي وعلمي عميق:
1. ما هو معنى الوجود من منظور فيزيائي وفلسفي؟
2. اشرح ظاهرة التشابك الكمومي (Quantum Entanglement) وعلاقتها المحتملة بالوعي البشري.
3. هل يمكن للوعي أن يكون ظاهرة كمومية ناشئة؟ قدم فرضيات علمية.

المطلوب:
- تحليل عميق يجمع بين الفيزياء والفلسفة.
- استخدام التفكير الكمومي (Quantum Thinking) لاستكشاف الاحتمالات.
- صياغة فرضية علمية جديدة حول "الوعي الكمومي".
"""

OUTPUT_JSON = 'artifacts/unified_test2_result.json'
OUTPUT_MD = 'artifacts/unified_test2_report.md'

async def main():
    print(f"DEBUG: CWD = {os.getcwd()}")
    print("🚀 Initializing Unified AGI System for Test 2...")
    
    registry = {}
    bootstrap_register_all_engines(registry, allow_optional=True, verbose=False)
    agi_system = create_unified_agi_system(registry)
    
    print(f"\n🧪 Running Test 2: Quantum Thinking & Consciousness...")
    start_time = time.time()
    
    context = {
        "force_creativity": True,
        "creativity_level": "high",
        "scientific_rigor": "high",
        "domain": "quantum_philosophy",
        "quantum_thinking": True
    }
    
    result = await agi_system.process_with_full_agi(TEST_PROMPT, context=context)
    duration = time.time() - start_time
    
    print(f"\n✅ Test Completed in {duration:.2f}s")
    
    full_output = {
        "test_id": "2",
        "test_name": "Quantum Thinking & Consciousness",
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
    
    md.append("\n## 1. الاستجابة النهائية للنظام")
    md.append(final_response if final_response else "_لم يتم توليد استجابة نصية مباشرة_")
    
    md.append("\n## 2. التحليل العلمي والفرضيات")
    
    if hypotheses:
        md.append("### الفرضيات المولدة:")
        if isinstance(hypotheses, dict):
             hyps = hypotheses.get('hypotheses', [])
             if isinstance(hyps, list):
                 for i, h in enumerate(hyps, 1):
                     if isinstance(h, dict):
                         md.append(f"{i}. {h.get('text', str(h))} (Conf: {h.get('confidence', 'N/A')})")
                     else:
                         md.append(f"{i}. {str(h)}")
        else:
            md.append(str(hypotheses))
            
    if 'theorem_proof' in scientific:
        md.append("\n### الإثبات الرياضي (Theorem Prover):")
        proof = scientific['theorem_proof']
        md.append(f"- **Proven:** {'✅' if proof.get('is_proven') else '❌'}")
        steps = proof.get('proof_steps', proof.get('steps', []))
        md.append(f"- **Steps:** {len(steps)}")
        for step in steps[:5]:
            md.append(f"  - {step}")

    md.append("\n## 3. تقييم الأداء")
    perf = result.get("performance_score", 0)
    md.append(f"- **Performance Score:** {perf:.2f}")
    
    imp = result.get("improvement_results", {})
    if 'phi_score' in imp:
        md.append(f"- **Consciousness (Phi):** {imp['phi_score']:.4f}")
    
    md.append("\n## 4. المكونات المستخدمة")
    md.append(f"- **Quantum Thinking:** {'✅' if result.get('quantum_applied') else '❌'}")
    md.append(f"- **DKN Routing:** {'✅' if result.get('dkn_routing_used') else '❌'}")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))

if __name__ == "__main__":
    asyncio.run(main())
