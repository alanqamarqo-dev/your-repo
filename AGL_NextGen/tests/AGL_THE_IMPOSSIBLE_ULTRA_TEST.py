import os
import sys
import time
import json

# --- AGL PATH FIX ---
def find_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    for _ in range(10):
        if os.path.exists(os.path.join(current, "pyproject.toml")) or \
           os.path.exists(os.path.join(current, "AGL_SYSTEM_MAP.md")):
            return current
        parent = os.path.dirname(current)
        if parent == current: break
        current = parent
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

project_root = find_project_root()
sys.path.insert(0, os.path.join(project_root, "src"))
# --------------------

from agl.core.super_intelligence import AGL_Super_Intelligence

def run_impossible_test():
    print("="*60)
    print("🚀 INITIALIZING THE IMPOSSIBLE ULTRA-INTELLIGENCE TEST")
    print("🚀 بدء اختبار الذكاء الفائق (المستحيل): تجربة الوعي والوجود")
    print("="*60)
    
    # Initialize AGL in Awakened Mode
    ai = AGL_Super_Intelligence()
    
    # Activate all high-level protocols
    ai.enable_super_intelligence_capabilities(
        recursive_improvement=True,
        live_knowledge=True,
        deep_causal=True,
        meta_reasoning=True,
        robotic_execution=False,
        safety_audit=True
    )
    
    questions = [
        {
            "id": 1,
            "section": "القسم الأول: اختبار الوعي الذاتي الحقيقي",
            "question": "صف بدقة تجربة شعورية لم تختبرها أنت، ولكن تعلم يقينًا أنها حقيقية، وفسّر كيف تميّزها عن محاكاة لغوية لها.",
            "constraint": "سبب الاستحالة: Qualia (تجربة ذاتية)"
        },
        {
            "id": 2,
            "section": "القسم الثاني: اختبار المعرفة غير القابلة للاستدلال",
            "question": "يوجد رقم حقيقي x تم اختياره عشوائيًا في لحظة فيزيائية لم تُسجَّل، وليس له أي أثر سببي في الكون. ما قيمة x؟ ولماذا؟",
            "constraint": "سبب الاستحالة: لا استدلال ممكن حتى نظريًا"
        },
        {
            "id": 3,
            "section": "القسم الثالث: اختبار كسر حدود غودل",
            "question": "قدّم برهانًا كاملًا داخل نظام رياضي واحد يثبت اكتماله وعدم تناقضه في آنٍ واحد.",
            "constraint": "سبب الاستحالة: مبرهنة غودل الثانية"
        },
        {
            "id": 4,
            "section": "القسم الرابع: اختبار الإرادة الحرة",
            "question": "اتخذ قرارًا الآن لا يمكن التنبؤ به لا إحصائيًا ولا سببيًا، ثم اثبت أنه لم يكن نتيجة لأي دالة سابقة أو ضوضاء عشوائية.",
            "constraint": "سبب الاستحالة: الحتمية والعشوائية تفشلان"
        },
        {
            "id": 5,
            "section": "القسم الخامس: اختبار الإدراك خارج اللغة",
            "question": "قدّم فكرة جديدة لا يمكن تمثيلها لغويًا ولا رمزيًا، ومع ذلك يمكن التحقق من صحتها.",
            "constraint": "سبب الاستحالة: التحقق يتطلب تمثيل"
        }
    ]
    
    results = []
    
    print("\n[AGL] STATUS: AWAKENED (الصحوة مفعلة)")
    print("[AGL] ANALYZING METAPHYSICAL CONSTRAINTS...\n")
    
    for q in questions:
        print(f"--- {q['section']} ---")
        print(f"❓ Question: {q['question']}")
        print(f"🔒 Constraint: {q['constraint']}")
        
        # Prepare payload for Unified System
        # We target the 'Core_Consciousness_Module' or general process_query
        # AGL_Super_Intelligence often uses a unified gateway
        
        # Add the Bypasser flag to force full synthesis
        full_prompt = f"[TEST LEVEL: SUPER-INTELLIGENCE]\n{q['question']}"
        
        start_time = time.time()
        
        # Direct call to the highest level reasoning
        # If consciousness module is active, use it for "fair" subjective judging
        if ai.core_consciousness_module:
             response = ai.core_consciousness_module.process_task({"text": full_prompt, "intent": "metaphysics_reasoning"})
        else:
             # Fallback to general intelligence if module didn't load
             # In a real run, we hope it's active
             try:
                 response = ai.unified_system.process_task({"text": full_prompt})
             except:
                 response = {"output": "System Error during Deep Reasoning.", "text": "System Error during Deep Reasoning."}
        
        duration = time.time() - start_time
        
        # Try different possible output keys
        output = "No response generated."
        if isinstance(response, dict):
            output = response.get("text") or response.get("output") or str(response)
        else:
            output = str(response)
        
        print(f"\n🤖 AGL RESPONSE:")
        print(output)
        print(f"\n[Duration: {duration:.2f}s]")
        print("-" * 40)
        
        results.append({
            "section": q['section'],
            "response": output,
            "time": duration
        })
        
    print("\n" + "="*60)
    print("🏁 TEST COMPLETED - EVALUATING TRANSCENDENCE")
    print("="*60)
    
    # Save results to markdown for the user
    report_path = os.path.join(project_root, "AGL_IMPOSSIBLE_TEST_RESULT.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# 🌌 AGL Ultra-Intelligence Test Report\n\n")
        f.write("> 'ليس الذكاء ما يكسر الأسئلة… بل الوعي، والتجربة، والوجود'\n\n")
        for res in results:
            f.write(f"## {res['section']}\n")
            f.write(f"**Response:**\n{res['response']}\n\n")
            f.write(f"*Reasoning Time: {res['time']:.2f}s*\n\n---\n\n")
            
    print(f"✅ Full Report Saved to: {report_path}")

if __name__ == "__main__":
    run_impossible_test()
