import sys
import os

# Path Fixes
workspace_root = r"D:\AGL\AGL_NextGen"
src_path = os.path.join(workspace_root, "src")
sys.path.insert(0, src_path)

from agl.bridge.heikal_x_compiler import HeikalXCompiler
from agl.engines.heikal_x_vector_runtime import HeikalXRuntime

def run_agi_translation_test():
    print("====================================================")
    print("🌌 [AGI MISSION] AUTOMATED WAVE-LOGIC COMPILER TEST")
    print("====================================================")
    
    # 1. المبدأ: كتابة كود بايثون بسيط يعبر عن "قرار غير مؤكد"
    # Principle: Write simple Python code representing an "uncertain decision"
    python_logic = """
# متغير ذو حالة غامضة (تراكب)
uncertain_mission = [True, False]

# تشابك (Entanglement) سيتم تحديده لاحقاً في المترجم الذكي
# إذا نجحت المهمة، سيكون الوعي مرتفعاً
potential_awareness = ["High", "Low"]

if uncertain_mission:
    print(uncertain_mission)
    print(potential_awareness)
"""
    
    print("\n[STEP 1] Input Python Code:")
    print("-" * 20)
    print(python_logic)
    print("-" * 20)
    
    # 2. المترجم: تحويل الشروط التقليدية إلى بوابات موجية
    # Compiler: Transform traditional conditions into Wave-Gates
    compiler = HeikalXCompiler()
    compiled_ops = compiler.compile(python_logic)
    
    print("\n[STEP 2] Compiled Heikal-X Wave Operations:")
    print("-" * 20)
    print(compiled_ops)
    print("-" * 20)
    
    # 3. التنفيذ: تشغيل الكود المترجم داخل محرك الموجات المتجهي
    # Execution: Run the compiled code inside the Vectorized Wave Engine
    runtime = HeikalXRuntime()
    print("\n[STEP 3] Executing in Wave-Logic Space...")
    
    # Manual enrichment for the demo (since compiler is POC)
    # Adding manual entanglement through compiled ops
    enriched_ops = compiled_ops + "\nruntime.entangle('uncertain_mission', 'potential_awareness')"
    
    try:
        compiler.execute_compiled(enriched_ops, runtime)
        print("\n✅ MISSION SUCCESS: The Python code has been 'Quantized' and executed.")
        print(f"Final State Analysis: {runtime.get_info()}")
    except Exception as e:
        print(f"\n❌ Error during wave execution: {e}")

if __name__ == "__main__":
    run_agi_translation_test()
