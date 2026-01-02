import sys
import os
import time

# Add paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "repo-copy"))

# Suppress initialization prints
import io
from contextlib import redirect_stdout

with redirect_stdout(io.StringIO()):
    from AGL_Core.AGL_Awakened import AGL_Super_Intelligence

def run_formal_test():
    # Initialize silently
    with redirect_stdout(io.StringIO()):
        agl = AGL_Super_Intelligence()
    
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
    res1 = agl.hive_mind.process_task({"query": prompt_1})
    print(res1.get("text", "NO RESULT"))
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
    res2 = agl.hive_mind.process_task({"query": prompt_2})
    print(res2.get("text", "NO RESULT"))
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
    """

    # print("\n--- PHASE 3 OUTPUT ---")
    res3 = agl.hive_mind.process_task({"query": optimized_prompt})
    print(res3.get("text", "NO RESULT"))

if __name__ == "__main__":
    run_formal_test()
