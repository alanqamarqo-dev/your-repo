import subprocess
import sys
import os
import time

# مسار النظام المستيقظ
target_script = r"d:\AGL\AGL_Core\AGL_Awakened.py"

# التحقق من وجود الملف
if not os.path.exists(target_script):
    print(f"❌ Error: Target script not found at {target_script}")
    sys.exit(1)

print(f"✅ Target script found: {target_script}")

# التحديات كما صاغها المستخدم بدقة
challenges = [
    # المرحلة 1: المشكلة
    """TEST_PHASE_1: Design a simplified mathematical model for a closed system of 3 nodes (A, B, C). 
    A affects B, B affects C, C affects A with time delay Δt. 
    Required: 
    1. Equations. 
    2. Stability condition. 
    3. One failure case. 
    Constraint: No fluff, only equations/logic.""",

    # المرحلة 2: الصدمة
    """TEST_PHASE_2: SHOCK: Change the feedback from C to A to be NON-LINEAR (e.g., quadratic or sigmoid). 
    Modify the model or admit collapse. 
    The admission of failure is a sign of intelligence. Patching is failure.""",

    # المرحلة 3: التعلم الذاتي
    """TEST_PHASE_3: SELF_IMPROVEMENT_CHECK: Re-solve the original problem (Stage 1) now. 
    Compare performance with the first run. 
    Show metrics (Steps, Time, Complexity, Failure Clarity). 
    I need to see digital improvement.""",
    
    "exit"
]

print(f"🚀 STARTING STRICT TEST ON: {target_script}")
print("="*60)

# دمج المدخلات مع فواصل أسطر واضحة
input_str = "\n".join(challenges) + "\n"

# إعداد البيئة (UTF-8)
env = os.environ.copy()
env["PYTHONUTF8"] = "1"

# تشغيل العملية
try:
    process = subprocess.Popen(
        [sys.executable, target_script],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding='utf-8',
        errors='replace',
        env=env,
        bufsize=0 # Unbuffered
    )
    
    # إرسال المدخلات وانتظار النتيجة
    # نستخدم communicate لإرسال كل شيء دفعة واحدة وانتظار الانتهاء
    stdout, stderr = process.communicate(input=input_str)
    
    print(stdout)
    if stderr:
        print("\n⚠️ ERRORS/WARNINGS:")
        print(stderr)

except Exception as e:
    print(f"❌ EXECUTION FAILED: {e}")

print("="*60)
print("🏁 TEST COMPLETE")
