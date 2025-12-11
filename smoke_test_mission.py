"""
اختبار دخان سريع للتحقق من اتصال mission_control_enhanced مع UnifiedAGI
"""
import asyncio
import sys
import os

# إضافة المسارات اللازمة
base = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(base, "repo-copy"))
sys.path.insert(0, os.path.join(base, "repo-copy", "dynamic_modules"))

async def run_smoke():
    try:
        import mission_control_enhanced as mc
    except Exception as e:
        print("IMPORT_ERROR", repr(e))
        return

    # نص تجريبي من المحتمل أن يفعّل الإبداع والفرضيات
    question = "كيف تؤثر الاحتمالات المتعددة على قراراتنا؟"
    print("Running smoke test with question:\n", question)
    try:
        # process_with_unified_agi قد تكون دالة async أو sync حسب النسخة
        proc = getattr(mc, 'process_with_unified_agi', None)
        if proc is None:
            print("MISSING_FUNCTION process_with_unified_agi in mission_control_enhanced")
            return

        # استدعاء الدالة (تحسب أنها async)
        result = await proc(question)

        # طباعة الخلاصة
        print("--- SMOKE RESULT KEYS ---")
        if isinstance(result, dict):
            keys = list(result.keys())
            print("keys:", keys)
            for k in ['final_response','hypothesis_applied','hypotheses','quantum_applied','quantum_result','creativity_auto_detected']:
                print(f"{k}:", result.get(k, '<missing>'))
            print("Response preview:\n", (result.get('final_response') or '')[:400])
        else:
            print("Result is not a dict:", type(result), repr(result))

    except Exception as e:
        print("RUNTIME_ERROR", repr(e))

if __name__ == '__main__':
    asyncio.run(run_smoke())
