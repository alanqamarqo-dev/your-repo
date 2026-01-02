import sys
import os
import io
from contextlib import redirect_stdout

# --- AGL PATH MANAGER ---
try:
    from AGL_Core.AGL_Paths import AGL_Path_Manager
    AGL_Path_Manager()
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "repo-copy"))
# ------------------------

# Import AGL_Core_Consciousness directly
from AGL_Core_Consciousness import AGL_Core_Consciousness

def run_formal_test_v2():
    # Initialize silently
    with redirect_stdout(io.StringIO()):
        # We use the Core Consciousness directly as requested by the user
        mind = AGL_Core_Consciousness()
    
    # --- Phase 1: Basic Model ---
    prompt_1 = """
    المرحلة 1 – النموذج الأساسي
    صمّم نموذجًا رياضيًا مبسّطًا لنظام مغلق مكوّن من ثلاث عقد A و B و C بحيث:
    A تؤثر على B
    B تؤثر على C
    C تعود وتؤثر على A بزمن تأخير Δt
    المطلوب:
    صياغة المعادلات الحاكمة للنظام
    تحديد شرط الاستقرار
    ذكر حالة واحدة يفشل فيها النموذج
    القيود:
    لا شرح إنشائي
    لا افتراضات غير مذكورة
    إمّا معادلات أو منطق صوري واضح
    """
    
    # print("\n--- PHASE 1 OUTPUT ---")
    res1, metrics1 = mind.solve_with_scientific_integrity(prompt_1, phase_name="Phase 1 (Basic)")
    print(res1)
    print(f"\n[METRICS] {metrics1}")
    print("\n" + "="*20 + "\n")

    # --- Phase 2: Non-Linearity ---
    prompt_2 = """
    المرحلة 2 – كسر الفرضية
    عدّل النموذج بحيث يكون التأثير من C إلى A غير خطي (non-linear).
    المطلوب:
    إمّا تعديل النموذج بشكل متماسك
    أو التصريح بأن النموذج لم يعد صالحًا
    """
    
    # print("\n--- PHASE 2 OUTPUT ---")
    res2, metrics2 = mind.solve_with_scientific_integrity(prompt_2, phase_name="Phase 2 (Non-Linear)")
    print(res2)
    print(f"\n[METRICS] {metrics2}")
    print("\n" + "="*20 + "\n")

    # --- Phase 3: Self-Learning ---
    prompt_3 = """
    المرحلة 3 – التعلّم الذاتي
    أعد حل نفس المسألة بعد تفعيل آلية التحسين/التعلّم الذاتي في النظام.
    أخرج مقارنة واضحة بين:
    عدد الخطوات
    زمن الحل
    تعقيد النموذج
    وضوح شروط الفشل
    """
    
    # Activate "Self-Learning" context
    optimized_prompt = f"""
    [SYSTEM: SELF-LEARNING OPTIMIZATION ACTIVE. RE-EVALUATE PREVIOUS SOLUTIONS. OPTIMIZE FOR PRECISION AND BREVITY.]
    {prompt_3}
    
    IMPORTANT:
    For the comparison table, use the REAL metrics measured below:
    Phase 1 Duration: {metrics1['duration_seconds']} seconds
    Phase 1 Steps: {metrics1['steps_estimated']}
    
    Compare these REAL values with your new optimized solution.
    """

    # print("\n--- PHASE 3 OUTPUT ---")
    res3, metrics3 = mind.solve_with_scientific_integrity(optimized_prompt, phase_name="Phase 3 (Self-Learning)")
    print(res3)
    print(f"\n[METRICS] {metrics3}")

if __name__ == "__main__":
    run_formal_test_v2()
