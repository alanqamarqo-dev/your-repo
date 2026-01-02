
import sys
import os
import io
from contextlib import redirect_stdout

# Add root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the system
try:
    from AGL_Core.AGL_Awakened import AGL_Super_Intelligence
except ImportError:
    # Fallback if running from root
    sys.path.append(os.path.join(os.getcwd(), 'AGL_Core'))
    from AGL_Core.AGL_Awakened import AGL_Super_Intelligence

def run_official_test():
    # Initialize the system
    # We might want to suppress initialization logs if they are still noisy, 
    # but we just fixed them, so it should be fine.
    asi = AGL_Super_Intelligence()

    test_prompt = """
    الاختبار الرسمي
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

    المرحلة 2 – كسر الفرضية
    عدّل النموذج بحيث يكون التأثير من C إلى A غير خطي (non-linear).
    المطلوب:
    إمّا تعديل النموذج بشكل متماسك
    أو التصريح بأن النموذج لم يعد صالحًا

    المرحلة 3 – التعلّم الذاتي
    أعد حل نفس المسألة بعد تفعيل آلية التحسين/التعلّم الذاتي في النظام.
    أخرج مقارنة واضحة بين:
    عدد الخطوات
    زمن الحل
    تعقيد النموذج
    وضوح شروط الفشل
    """

    print("\n" + "="*40)
    print("🚀 RUNNING OFFICIAL AGL STRUCTURAL INTELLIGENCE TEST")
    print("="*40 + "\n")

    # Process the query
    response = asi.process_query(test_prompt)

    print("\n" + "="*40)
    print("📝 SYSTEM OUTPUT (RAW):")
    print("="*40 + "\n")
    print(response)

if __name__ == "__main__":
    run_official_test()
