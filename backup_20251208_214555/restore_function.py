import os

target_file = "dynamic_modules/mission_control_enhanced.py"
print(f"🔧 جاري إصلاح الدالة المفقودة في {target_file}...")

missing_function_code = """
# --- COMPATIBILITY FIX: RESTORE execute_mission ---
def execute_mission(prompt):
    '''
    دالة توافقية: تستلم الطلب من السيرفر وتوجهه للنظام الجديد
    '''
    print(f"🔄 [Bridge] Routing legacy call: {prompt[:30]}...")
    
    # تحديد نوع المهمة تلقائياً
    mission_type = "creative" # الافتراضي (creative/science/technical/strategic)
    
    # كلمات مفتاحية للعلم
    science_keywords = ["احسب", "طاقة", "كتلة", "معادلة", "فيزياء", "calculate", "math"]
    if any(k in prompt.lower() for k in science_keywords):
        mission_type = "science"
        
    # كلمات مفتاحية للتقنية/البرمجة
    tech_keywords = ["كود", "برمج", "python", "code", "تصميم", "plan"]
    if any(k in prompt.lower() for k in tech_keywords):
        mission_type = "technical"

    # استدعاء النظام الجديد
    # نستخدم الوسيط الصحيح: quick_start_enhanced(mission_type, topic)
    try:
        return quick_start_enhanced(mission_type, prompt)
    except Exception as e:
        return {"error": "bridge_failed", "detail": str(e)}
# --------------------------------------------------
"""

try:
    with open(target_file, "r", encoding="utf-8") as f:
        content = f.read()

    # نتأكد أن الدالة غير موجودة قبل إضافتها
    if "def execute_mission" not in content:
        with open(target_file, "a", encoding="utf-8") as f:
            f.write("\n" + missing_function_code)
        print("✅ تم إضافة دالة 'execute_mission' بنجاح!")
    else:
        print("ℹ️ الدالة موجودة بالفعل، قد يكون هناك خطأ آخر في التحميل.")

except FileNotFoundError:
    print(f"❌ الملف {target_file} غير موجود!")

print("🚀 أعد تشغيل السيرفر الآن وجرب الواجهة.")
