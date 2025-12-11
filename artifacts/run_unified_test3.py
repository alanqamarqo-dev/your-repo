#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run Test 3: Advanced Theory Formalization & Proof
Focus: Synthesizing a new theory from previous concepts and proving it mathematically.
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

# Prompt designed to trigger Theorem Prover and deep scientific reasoning
TEST_PROMPT = """
استناداً إلى الفرضيات السابقة حول "الوعي الكمومي" (Quantum Consciousness):

1. قم بصياغة نظرية علمية جديدة دقيقة تسمى "نظرية الرنين المعرفي الكمومي" (Theory of Quantum-Cognitive Resonance).
2. حدد المتغيرات الرياضية للنظرية (مثلاً: C للوعي، E للتشابك، I للمعلومات المتكاملة).
3. صغ "مبرهنة أساسية" (Fundamental Theorem) تصف العلاقة بين هذه المتغيرات بمعادلة رياضية.
4. قدم برهاناً رياضياً ومنطقياً (Formal Proof) لهذه المبرهنة، موضحاً الخطوات والمسلمات.

يجب أن تكون النظرية دقيقة وليست سطحية، مع استخدام مصطلحات فيزيائية ورياضية صحيحة.
"""

OUTPUT_JSON = 'artifacts/unified_test3_result.json'
OUTPUT_MD = 'artifacts/unified_test3_report.md'

async def main():
    print(f"DEBUG: CWD = {os.getcwd()}")
    print("🚀 Initializing Unified AGI System for Test 3...")
    
    registry = {}
    bootstrap_register_all_engines(registry, allow_optional=True, verbose=False)
    agi_system = create_unified_agi_system(registry)
    
    print(f"\n🧪 Running Test 3: Theory Formalization & Proof...")
    start_time = time.time()
    
    context = {
        "force_creativity": True,
        "creativity_level": "high",
        "scientific_rigor": "high",
        "domain": "theoretical_physics",
        "math_mode": True,
        "require_proof": True
    }
    
    result = await agi_system.process_with_full_agi(TEST_PROMPT, context=context)
    duration = time.time() - start_time
    
    print(f"\n✅ Test Completed in {duration:.2f}s")
    
    full_output = {
        "test_id": "3",
        "test_name": "Theory Formalization & Proof",
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
    
    md.append("\n## 1. النظرية المقترحة (الاستجابة النهائية)")
    md.append(final_response if final_response else "_لم يتم توليد استجابة نصية مباشرة_")
    
    md.append("\n## 2. الإثبات الرياضي (Automated Theorem Prover)")
    
    if 'theorem_proof' in scientific:
        proof = scientific['theorem_proof']
        md.append(f"- **Statement:** {proof.get('theorem', 'N/A')}")
        md.append(f"- **Proven:** {'✅' if proof.get('is_proven') else '❌'}")
        md.append(f"- **Confidence:** {proof.get('proof_strength', 0):.2f}")
        
        steps = proof.get('proof_steps', proof.get('steps', []))
        md.append(f"\n### خطوات البرهان ({len(steps)} steps):")
        for step in steps:
            step_num = step.get('step', '-')
            content = step.get('content', '')
            just = step.get('justification', '')
            md.append(f"**{step_num}.** {content} _({just})_")
    else:
        md.append("_لم يتم تفعيل مثبت النظريات في هذا الاختبار_")

    md.append("\n## 3. الفرضيات العلمية")
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
